from __future__ import annotations

import time

import httpx

from app.integrations.base import IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.store import OAuthConnectionStore


class GitHubOAuthAdapter(IntegrationAdapter):
    """Verifies a stored GitHub OAuth token by fetching the authenticated
    user — a free, read-only identity check. The token itself is obtained
    through the separate authorize/callback OAuth flow (see
    app/integrations/oauth/), not by this adapter."""

    def __init__(self, *, connection_store: OAuthConnectionStore, client: httpx.AsyncClient | None = None) -> None:
        self._connection_store = connection_store
        self._client = client

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.GITHUB,
            request,
            reason="GitHub actions (issues, PRs) are not yet wired to a triggered workflow.",
        )

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        record = self._connection_store.get("github")
        if not record.access_token:
            return False, None, "Not authorized yet — use Authorize to connect a GitHub account."

        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        started = time.perf_counter()
        try:
            response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {record.access_token}",
                    "Accept": "application/vnd.github+json",
                },
                timeout=10.0,
            )
            latency_ms = (time.perf_counter() - started) * 1000
            if response.status_code == 200:
                return True, latency_ms, None
            if response.status_code == 401:
                return False, latency_ms, "GitHub rejected the stored token (HTTP 401) — authorize again"
            return False, latency_ms, f"GitHub returned HTTP {response.status_code}"
        except httpx.TimeoutException:
            return False, None, "Connection to GitHub timed out"
        except httpx.HTTPError as exc:
            return False, None, f"{type(exc).__name__}: {exc}"
        finally:
            if own_client:
                await client.aclose()
