from __future__ import annotations

import httpx

from app.integrations.base import IntegrationAdapter, unsupported_execute_result
from app.integrations.models import IntegrationProvider, IntegrationRequest, IntegrationResult
from app.integrations.oauth.store import OAuthConnectionStore
from app.integrations.oauth.verify import oauth_get, verify_oauth_identity


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

    async def run_capability(self, capability_id: str, arguments: dict) -> object:
        """`identity.account.read` and `repo.metadata.read`. Write and
        high-risk capabilities stay unwired — see github.py's adapter for
        the same reasoning."""

        def headers(token: str) -> dict[str, str]:
            return {"Authorization": f"Bearer {token}"}

        if capability_id == "identity.account.read":
            return await oauth_get(
                provider_id="gitlab",
                provider_name="GitLab",
                url="https://gitlab.com/api/v4/user",
                connection_store=self._connection_store,
                build_headers=headers,
                client=self._client,
            )
        if capability_id == "repo.metadata.read":
            projects = await oauth_get(
                provider_id="gitlab",
                provider_name="GitLab",
                url="https://gitlab.com/api/v4/projects?membership=true&per_page=100",
                connection_store=self._connection_store,
                build_headers=headers,
                client=self._client,
            )
            return [
                {"path_with_namespace": p["path_with_namespace"], "visibility": p["visibility"], "default_branch": p.get("default_branch")}
                for p in projects
            ]
        return await super().run_capability(capability_id, arguments)

    async def test_connection(self) -> tuple[bool, float | None, str | None]:
        return await verify_oauth_identity(
            provider_id="gitlab",
            provider_name="GitLab",
            identity_url="https://gitlab.com/api/v4/user",
            connection_store=self._connection_store,
            build_headers=lambda token: {"Authorization": f"Bearer {token}"},
            client=self._client,
        )
