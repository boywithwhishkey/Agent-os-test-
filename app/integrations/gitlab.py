from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from app.integrations.base import CapabilityNotWired, IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.config import OAUTH_PROVIDERS
from app.integrations.oauth.service import request_with_oauth_refresh
from app.integrations.oauth.store import OAuthConnectionStore
from app.integrations.oauth.verify import verify_oauth_identity


class GitLabOAuthAdapter(IntegrationAdapter):
    """Verifies a stored GitLab OAuth token via `GET /api/v4/user` — a
    free, read-only identity check. The token is obtained through the
    separate authorize/callback OAuth flow (see app/integrations/oauth/)."""

    def __init__(self, *, connection_store: OAuthConnectionStore, client: httpx.AsyncClient | None = None) -> None:
        self._connection_store = connection_store
        self._client = client

    async def execute(self, request: IntegrationRequest) -> IntegrationResult:
        return unsupported_execute_result(
            IntegrationProvider.GITLAB,
            request,
            reason="GitLab actions (issues, MRs) are not yet wired to a triggered workflow.",
        )

    async def run_capability(self, capability_id: str, arguments: dict[str, Any]) -> object:
        if capability_id == "identity.account.read":
            return await self._get("https://gitlab.com/api/v4/user")
        if capability_id in {"repo.metadata.read", "repo.content.read"}:
            project = self._project(arguments)
            project_id = quote(project, safe="")
            if capability_id == "repo.metadata.read":
                return await self._get(f"https://gitlab.com/api/v4/projects/{project_id}")
            path = quote(self._content_path(arguments), safe="")
            ref = self._ref(arguments)
            return await self._get(
                f"https://gitlab.com/api/v4/projects/{project_id}/repository/files/{path}",
                params={"ref": ref},
            )
        raise CapabilityNotWired(f"{type(self).__name__} has no operation for {capability_id}")

    @staticmethod
    def _project(arguments: dict[str, Any]) -> str:
        project = arguments.get("project")
        if (
            not isinstance(project, str)
            or not project.strip()
            or len(project) > 255
            or project.startswith("/")
            or ".." in project.split("/")
        ):
            raise ValueError("repo metadata/content requires a safe GitLab project path")
        return project.strip()

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
    def _ref(arguments: dict[str, Any]) -> str:
        ref = arguments.get("ref", "main")
        if not isinstance(ref, str) or not ref.strip() or len(ref) > 255 or any(ord(char) < 32 for char in ref):
            raise ValueError("repo.content.read ref must be a valid GitLab branch or tag")
        return ref.strip()

    async def _get(self, url: str, *, params: dict[str, str] | None = None) -> dict[str, Any] | list[Any]:
        record = self._connection_store.get("gitlab")
        if not record.access_token:
            raise RuntimeError("Not authorized yet — use Authorize to connect a GitLab account.")
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        try:
            response = await request_with_oauth_refresh(
                OAUTH_PROVIDERS["gitlab"],
                connection_store=self._connection_store,
                client=client,
                send=lambda token: client.get(
                    url,
                    params=params,
                    headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                    timeout=10.0,
                ),
            )
            if response.status_code >= 400:
                if response.status_code == 401:
                    raise RuntimeError("GitLab rejected the stored token (HTTP 401) — authorize again")
                raise RuntimeError(f"GitLab returned HTTP {response.status_code}")
            try:
                body = response.json()
            except ValueError as exc:
                raise RuntimeError("GitLab returned a non-JSON response") from exc
            if not isinstance(body, (dict, list)):
                raise TypeError("GitLab returned an invalid response")
            return body
        except httpx.TimeoutException as exc:
            raise RuntimeError("GitLab request timed out") from exc
        except httpx.HTTPError as exc:
            raise RuntimeError(f"GitLab request failed: {type(exc).__name__}") from exc
        finally:
            if own_client:
                await client.aclose()

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        return await verify_oauth_identity(
            provider_id="gitlab",
            provider_name="GitLab",
            identity_url="https://gitlab.com/api/v4/user",
            connection_store=self._connection_store,
            build_headers=lambda token: {"Authorization": f"Bearer {token}"},
            client=self._client,
        )
