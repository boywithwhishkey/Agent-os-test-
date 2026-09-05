from __future__ import annotations

import httpx
import pytest

from app.integrations.oauth.store import OAuthConnectionStore
from app.integrations.salesforce import SalesforceOAuthAdapter


def _store() -> OAuthConnectionStore:
    store = OAuthConnectionStore()
    store.record_success("salesforce", access_token="salesforce-access-token", token_type="Bearer", scope="api")
    return store


@pytest.mark.anyio
async def test_salesforce_identity_and_contacts_use_fixed_soql() -> None:
    seen: list[tuple[str, str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.url.path, request.url.params["q"], request.headers["authorization"]))
        return httpx.Response(200, json={"records": [{"Id": "org-1", "Name": "Demo"}], "totalSize": 1})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = SalesforceOAuthAdapter(
            instance_url="https://example.my.salesforce.com",
            connection_store=_store(),
            client=client,
        )
        identity = await adapter.run_capability("identity.account.read", {})
        contacts = await adapter.run_capability("crm.contact.list", {"limit": 5})
        deals = await adapter.run_capability("crm.deal.list", {"limit": 7})
    finally:
        await client.aclose()

    assert identity["records"][0]["Id"] == "org-1"
    assert contacts["totalSize"] == 1
    assert deals["totalSize"] == 1
    assert seen == [
        (
            "/services/data/v61.0/query",
            "SELECT Id, Name FROM Organization LIMIT 1",
            "Bearer salesforce-access-token",
        ),
        (
            "/services/data/v61.0/query",
            "SELECT Id, FirstName, LastName, Email FROM Contact LIMIT 5",
            "Bearer salesforce-access-token",
        ),
        (
            "/services/data/v61.0/query",
            "SELECT Id, Name, StageName, Amount, CloseDate FROM Opportunity ORDER BY LastModifiedDate DESC LIMIT 7",
            "Bearer salesforce-access-token",
        ),
    ]


@pytest.mark.anyio
async def test_salesforce_missing_connection_is_explicit() -> None:
    adapter = SalesforceOAuthAdapter(
        instance_url="https://example.my.salesforce.com", connection_store=OAuthConnectionStore()
    )
    connected, latency_ms, error = await adapter.test_connection()
    assert connected is False
    assert latency_ms is not None
    assert error == "Not authorized yet — use Authorize to connect a Salesforce account."


@pytest.mark.anyio
async def test_salesforce_contact_update_uses_sobject_patch() -> None:
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["auth"] = request.headers["authorization"]
        seen["body"] = request.content
        return httpx.Response(204)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await SalesforceOAuthAdapter(
            instance_url="https://example.my.salesforce.com",
            connection_store=_store(),
            client=client,
        ).run_capability(
            "crm.contact.update",
            {"contact_id": "003000000000001", "fields": {"FirstName": "Ada", "MobilePhone": "+1 555 0100"}},
        )
    finally:
        await client.aclose()

    assert result == {"id": "003000000000001", "updated": True}
    assert seen == {
        "method": "PATCH",
        "path": "/services/data/v61.0/sobjects/Contact/003000000000001",
        "auth": "Bearer salesforce-access-token",
        "body": b'{"FirstName":"Ada","MobilePhone":"+1 555 0100"}',
    }


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"contact_id": "bad/id", "fields": {"FirstName": "A"}}, "contact_id"),
        ({"contact_id": "003000000000001", "fields": {}}, "1-20"),
        ({"contact_id": "003000000000001", "fields": {"Bad-Name": "A"}}, "safe identifiers"),
        ({"contact_id": "003000000000001", "fields": {"Tags": []}}, "scalar JSON"),
    ],
)
def test_salesforce_contact_update_arguments_are_validated(
    arguments: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        SalesforceOAuthAdapter._contact_update_payload(arguments)


def test_salesforce_validates_instance_and_limit() -> None:
    with pytest.raises(RuntimeError, match="SALESFORCE_INSTANCE_URL"):
        SalesforceOAuthAdapter(connection_store=OAuthConnectionStore())
    adapter = SalesforceOAuthAdapter(
        instance_url="https://example.my.salesforce.com", connection_store=OAuthConnectionStore()
    )
    with pytest.raises(ValueError, match="between 1 and 200"):
        adapter._limit({"limit": 201})
