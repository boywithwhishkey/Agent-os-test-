from __future__ import annotations

import time
from typing import Any
from urllib.parse import quote

import httpx

from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore


class GitHubOAuthAdapter(IntegrationAdapter):
    """Run fixed, bounded GitHub identity, repository, and issue operations."""

    def __init__(self, *, connection_store: OAuthConnectionStore, client: httpx.AsyncClient | None = None) -> None:
        self._connection_store = connection_store
        self._client = client

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.GITHUB,
            request,
            reason="GitHub actions must use governed canonical capabilities.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._get("https://api.github.com/user")
        if capability_id in {"repo.metadata.read", "repo.content.read"}:
            owner, repo = self._repository(arguments)
            if capability_id == "repo.metadata.read":
                return await self._get(f"https://api.github.com/repos/{owner}/{repo}")
            encoded_path = quote(self._content_path(arguments), safe="/")
            return await self._get(f"https://api.github.com/repos/{owner}/{repo}/contents/{encoded_path}")
        if capability_id == "repo.issue.create":
            owner, repo = self._repository(arguments)
            return await self._post(
                f"https://api.github.com/repos/{owner}/{repo}/issues",
                self._issue_payload(arguments),
            )
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @staticmethod
    def _repository(arguments: dict[str, Any]) -> tuple[str, str]:
        owner = arguments.get("owner")
        repo = arguments.get("repo")
        if (
            not isinstance(owner, str)
            or not owner.strip()
            or len(owner) > 100
            or "/" in owner
            or ".." in owner
        ):
            raise ValueError("repo metadata/content requires a valid GitHub owner")
        if (
            not isinstance(repo, str)
            or not repo.strip()
            or len(repo) > 100
            or "/" in repo
            or ".." in repo
        ):
            raise ValueError("repo metadata/content requires a valid GitHub repository")
        return owner.strip(), repo.strip()

    @staticmethod
    def _content_path(arguments: dict[str, Any]) -> str:
        path = arguments.get("path", "README.md")
        if (
            not isinstance(path, str)
            or not path.strip()
            or len(path) > 1000
            or path.startswith("/")
            or ".." in path.split("/")
        ):
            raise ValueError("repo.content.read requires a safe repository-relative path")
        return path.strip()

    @staticmethod
    def _issue_payload(arguments: dict[str, Any]) -> dict[str, Any]:
        title = arguments.get("title")
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 256:
            raise ValueError("repo.issue.create requires a title of 256 characters or fewer")
        payload: dict[str, Any] = {"title": title.strip()}
        body = arguments.get("body")
        if body is not None:
            if not isinstance(body, str) or len(body) > 65_536:
                raise ValueError("repo.issue.create body must be 65536 characters or fewer")
            payload["body"] = body
        labels = arguments.get("labels")
        if labels is not None:
            if (
                not isinstance(labels, list)
                or len(labels) > 20
                or any(
                    not isinstance(label, str) or not 1 <= len(label.strip()) <= 100
                    for label in labels
                )
            ):
                raise ValueError("repo.issue.create labels must contain at most 20 short strings")
            payload["labels"] = [label.strip() for label in labels]
        return payload

    async def _get(self, url: str) -> dict[str, Any] | list[Any]:
        record = self._connection_store.get("github")
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a GitHub account.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["github"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.get(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                    },
                    timeout=10.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("GitHub rejected the stored token (HTTP 401) — authorize again")
                raise RuntimeError(f"GitHub returned HTTP {response.status_code}")
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("GitHub returned a non-JSON response") from exc
            if not isinstance(body, (dict, list)):
                raise TypeError("GitHub returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("GitHub request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"GitHub request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def _post(self, url: str, payload: dict[str, Any]) -> dict[str, Any] | list[Any]:
        record = self._connection_store.get("github")
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a GitHub account.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["github"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.post(
                    url,
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                        "X-GitHub-Api-Version": "2022-11-28",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                    timeout=10.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("GitHub rejected the stored token (HTTP 401) — authorize again")
                raise RuntimeError(f"GitHub returned HTTP {response.status_code}")
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("GitHub returned a non-JSON response") from exc
            if not isinstance(body, (dict, list)):
                raise TypeError("GitHub returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("GitHub request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"GitHub request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        record = self._connection_store.get("github")
        if not record.access_token:
            return False, None, "Not authorized yet — use Authorize to connect a GitHub account."

        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        started = time.perf_counter()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["github"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.get(
                    "https://api.github.com/user",
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Accept": "application/vnd.github+json",
                    },
                    timeout=10.0,
                ),
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
