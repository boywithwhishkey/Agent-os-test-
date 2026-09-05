from __future__ import annotations

import httpx
import pytest

from app.integrations.hubspot import HubSpotOAuthAdapter
from app.integrations.oauth.store import OAuthConnectionStore


def _store() -> OAuthConnectionStore:
    store = OAuthConnectionStore()
    store.record_success(
        "hubspot", access_token="hubspot-access-token", token_type="Bearer", scope="read"
    )
    return store


@pytest.mark.anyio
async def test_hubspot_identity_and_contacts_use_fixed_api_calls() -> None:
    seen: list[tuple[str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.url.path, request.url.query.decode()))
        assert request.headers["authorization"] == "Bearer hubspot-access-token"
        if request.url.path.endswith("/details"):
            return httpx.Response(200, json={"portalId": 123})
        return httpx.Response(200, json={"results": [{"id": "contact-1"}], "total": 1})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = HubSpotOAuthAdapter(connection_store=_store(), client=client)
        identity = await adapter.run_capability("identity.account.read", {})
        contacts = await adapter.run_capability("crm.contact.list", {"limit": 10})
    finally:
        await client.aclose()

    assert identity["portalId"] == 123
    assert contacts["results"][0]["id"] == "contact-1"
    assert seen == [
        ("/account-info/v3/details", ""),
        ("/crm/v3/objects/contacts", "limit=10&properties=email%2Cfirstname%2Clastname"),
    ]


@pytest.mark.anyio
async def test_hubspot_missing_connection_is_explicit() -> None:
    adapter = HubSpotOAuthAdapter(connection_store=OAuthConnectionStore())
    connected, latency_ms, error = await adapter.test_connection()
    assert connected is False
    assert latency_ms is not None
    assert error == "Not authorized yet — use Authorize to connect a HubSpot account."


@pytest.mark.anyio
async def test_hubspot_contact_update_uses_patch_and_email_lookup() -> None:
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["query"] = request.url.query.decode()
        seen["auth"] = request.headers["authorization"]
        seen["body"] = request.content
        return httpx.Response(200, json={"id": "contact-1", "properties": {"firstname": "Ada"}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await HubSpotOAuthAdapter(connection_store=_store(), client=client).run_capability(
            "crm.contact.update",
            {"email": "ada@example.com", "properties": {"firstname": "Ada", "lastname": "Lovelace"}},
        )
    finally:
        await client.aclose()

    assert result["id"] == "contact-1"
    assert seen == {
        "method": "PATCH",
        "path": "/crm/v3/objects/contacts/ada@example.com",
        "query": "idProperty=email",
        "auth": "Bearer hubspot-access-token",
        "body": b'{"properties":{"firstname":"Ada","lastname":"Lovelace"}}',
    }


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"contact_id": "1", "email": "a@example.com", "properties": {"firstname": "A"}}, "exactly one"),
        ({"contact_id": "1", "properties": {}}, "1-20"),
        ({"contact_id": "1", "properties": {"bad-name": "A"}}, "safe identifiers"),
        ({"email": "bad", "properties": {"firstname": "A"}}, "valid HubSpot contact email"),
    ],
)
def test_hubspot_contact_update_arguments_are_validated(
    arguments: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        HubSpotOAuthAdapter._contact_update_payload(arguments)


def test_hubspot_contact_limit_is_bounded() -> None:
    adapter = HubSpotOAuthAdapter(connection_store=OAuthConnectionStore())
    with pytest.raises(ValueError, match="between 1 and 100"):
        adapter._limit({"limit": 101})
