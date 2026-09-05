from __future__ import annotations

import hashlib
import hmac
import time
from datetime import UTC, datetime
from typing import Any

import httpx

from app.core.config import settings
from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult

_REGION_ENDPOINTS = {
    "na": ("sellingpartnerapi-na.amazon.com", "us-east-1"),
    "eu": ("sellingpartnerapi-eu.amazon.com", "eu-west-1"),
    "fe": ("sellingpartnerapi-fe.amazon.com", "us-west-2"),
}


class AmazonSPAPIAdapter(IntegrationAdapter):
    """Signed, read-only Amazon SP-API seller identity adapter."""

    def __init__(
        self,
        *,
        lwa_client_id: str | None = None,
        lwa_client_secret: str | None = None,
        lwa_refresh_token: str | None = None,
        aws_access_key_id: str | None = None,
        aws_secret_access_key: str | None = None,
        aws_session_token: str | None = None,
        region: str | None = None,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.lwa_client_id = lwa_client_id or settings.amazon_lwa_client_id or ""
        self.lwa_client_secret = lwa_client_secret or settings.amazon_lwa_client_secret or ""
        self.lwa_refresh_token = lwa_refresh_token or settings.amazon_lwa_refresh_token or ""
        self.aws_access_key_id = aws_access_key_id or settings.amazon_aws_access_key_id or ""
        self.aws_secret_access_key = aws_secret_access_key or settings.amazon_aws_secret_access_key or ""
        self.aws_session_token = aws_session_token or settings.amazon_aws_session_token
        self.region_name = (region or settings.amazon_region).lower().strip()
        self._client = client
        if self.region_name not in _REGION_ENDPOINTS:
            raise RuntimeError("AMAZON_REGION must be one of na, eu, or fe")
        required = {
            "AMAZON_LWA_CLIENT_ID": self.lwa_client_id,
            "AMAZON_LWA_CLIENT_SECRET": self.lwa_client_secret,
            "AMAZON_LWA_REFRESH_TOKEN": self.lwa_refresh_token,
            "AMAZON_AWS_ACCESS_KEY_ID": self.aws_access_key_id,
            "AMAZON_AWS_SECRET_ACCESS_KEY": self.aws_secret_access_key,
        }
        missing = next((name for name, value in required.items() if not value.strip()), None)
        if missing:
            raise RuntimeError(f"{missing} is required")
        self._cached_token: str | None = None
        self._cached_token_expires_at = 0.0

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.AMAZON,
            request,
            reason="Amazon mutations are not enabled; use the governed seller identity capability.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id != "identity.account.read":
            raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")
        token = await self._lwa_access_token()
        return await self._signed_get(
            "/sellers/v1/marketplaceParticipations",
            access_token=token,
        )

    async def _lwa_access_token(self) -> str:
        if self._cached_token and time.monotonic() < self._cached_token_expires_at:
            return self._cached_token
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.post(
                "https://api.amazon.com/auth/o2/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.lwa_refresh_token,
                    "client_id": self.lwa_client_id,
                    "client_secret": self.lwa_client_secret,
                },
                timeout=10.0,
            )
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Amazon LWA returned a non-JSON response") from exc
            if response.status_code >= 400:
                raise RuntimeError(f"Amazon LWA returned HTTP {response.status_code}")
            token = body.get("access_token") if isinstance(body, dict) else None
            if not isinstance(token, str) or not token:
                raise RuntimeError("Amazon LWA did not return an access token")
            expires_in = body.get("expires_in", 3600)
            self._cached_token = token
            self._cached_token_expires_at = time.monotonic() + max(float(expires_in) - 60, 60)
            return token
        except httpx.TimeoutException as exc:
            raise RuntimeError("Amazon LWA request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Amazon LWA request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def _signed_get(self, path: str, *, access_token: str) -> dict[str, Any]:
        host, aws_region = _REGION_ENDPOINTS[self.region_name]
        now = datetime.now(UTC)
        amz_date = now.strftime("%Y%m%dT%H%M%SZ")
        date_stamp = now.strftime("%Y%m%d")
        payload_hash = hashlib.sha256(b"").hexdigest()
        headers: dict[str, str] = {
            "host": host,
            "x-amz-access-token": access_token,
            "x-amz-date": amz_date,
        }
        if self.aws_session_token:
            headers["x-amz-security-token"] = self.aws_session_token
        canonical_headers = "".join(f"{key}:{' '.join(value.strip().split())}\n" for key, value in sorted(headers.items()))
        signed_headers = ";".join(sorted(headers))
        canonical_request = f"GET\n{path}\n\n{canonical_headers}\n{signed_headers}\n{payload_hash}"
        credential_scope = f"{date_stamp}/{aws_region}/execute-api/aws4_request"
        string_to_sign = (
            f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n"
            f"{hashlib.sha256(canonical_request.encode()).hexdigest()}"
        )
        signing_key = self._signing_key(date_stamp, aws_region)
        signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()
        authorization = (
            "AWS4-HMAC-SHA256 "
            f"Credential={self.aws_access_key_id}/{credential_scope}, "
            f"SignedHeaders={signed_headers}, Signature={signature}"
        )
        request_headers = {**headers, "Authorization": authorization}
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await client.get(f"https://{host}{path}", headers=request_headers, timeout=10.0)
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("Amazon SP-API returned a non-JSON response") from exc
            if response.status_code >= 400:
                raise RuntimeError(f"Amazon SP-API returned HTTP {response.status_code}")
            if not isinstance(body, dict):
                raise TypeError("Amazon SP-API returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("Amazon SP-API request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"Amazon SP-API request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    def _signing_key(self, date_stamp: str, aws_region: str) -> bytes:
        def sign(key: bytes, value: str) -> bytes:
            return hmac.new(key, value.encode(), hashlib.sha256).digest()

        date_key = sign(("AWS4" + self.aws_secret_access_key).encode(), date_stamp)
        region_key = sign(date_key, aws_region)
        service_key = sign(region_key, "execute-api")
        return sign(service_key, "aws4_request")

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        started = time.perf_counter()
        try:
            await self.run_capability("identity.account.read", {})
            return True, (time.perf_counter() - started) * 1000, None
        except RuntimeError as exc:
            return False, (time.perf_counter() - started) * 1000, str(exc)
