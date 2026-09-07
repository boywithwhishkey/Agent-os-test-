from __future__ import annotations

import json

import httpx
import pytest

from app.core.config import settings
from app.integrations.factory import is_provider_configured
from app.integrations.google_contacts import GoogleContactsOAuthAdapter
from app.integrations.models import IntegrationProvider
from app.integrations.oauth.store import OAuthConnectionStore


def _connected_store() -> OAuthConnectionStore:
    store = OAuthConnectionStore()
    store.record_success(
        IntegrationProvider.GOOGLE_CONTACTS.value,
        access_token="google-contacts-token",
        token_type="Bearer",
        scope="contacts",
    )
    return store


def test_google_contacts_uses_shared_google_oauth_configuration(monkeypatch) -> None:
    monkeypatch.setattr(settings, "google_oauth_client_id", "client-id")
    monkeypatch.setattr(settings, "google_oauth_client_secret", "client-secret")
    assert is_provider_configured(IntegrationProvider.GOOGLE_CONTACTS) is True


@pytest.mark.anyio
async def test_google_contacts_identity_list_and_create_use_people_api() -> None:
    seen: list[tuple[str, str, str, dict[str, object] | None]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        payload = json.loads(request.content) if request.content else None
        seen.append((request.method, request.url.path, request.url.query.decode(), payload))
        assert request.headers["authorization"] == "Bearer google-contacts-token"
        if request.url.path.endswith("userinfo"):
            return httpx.Response(200, json={"email": "person@example.com", "sub": "user-1"})
        if request.method == "GET":
            return httpx.Response(200, json={"connections": [{"resourceName": "people/c1"}]})
        return httpx.Response(200, json={"resourceName": "people/c2", "names": [{"givenName": "Ada"}]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = GoogleContactsOAuthAdapter(connection_store=_connected_store(), client=client)
        identity = await adapter.run_capability("identity.account.read", {})
        listed = await adapter.run_capability("crm.contact.list", {"limit": 7})
        created = await adapter.run_capability(
            "crm.contact.create",
            {
                "given_name": "Ada",
                "family_name": "Lovelace",
                "email": "ada@example.com",
                "phone": "+1 555 0100",
                "organization": "THYNACT",
            },
        )
    finally:
        await client.aclose()

    assert identity["email"] == "person@example.com"
    assert listed["connections"][0]["resourceName"] == "people/c1"
    assert created["resourceName"] == "people/c2"
    assert seen == [
        ("GET", "/oauth2/v3/userinfo", "", None),
        (
            "GET",
            "/v1/people/me/connections",
            "personFields=names%2CemailAddresses%2CphoneNumbers%2Corganizations%2Cmetadata&pageSize=7&sortOrder=LAST_MODIFIED_ASCENDING",
            None,
        ),
        (
            "POST",
            "/v1/people:createContact",
            "personFields=names%2CemailAddresses%2CphoneNumbers%2Corganizations%2Cmetadata",
            {
                "names": [{"givenName": "Ada", "familyName": "Lovelace"}],
                "emailAddresses": [{"value": "ada@example.com"}],
                "phoneNumbers": [{"value": "+1 555 0100"}],
                "organizations": [{"name": "THYNACT"}],
            },
        ),
    ]


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"given_name": ""}, "given_name"),
        ({"given_name": "Ada", "email": "not-an-email"}, "email"),
        ({"given_name": "Ada", "phone": "\n"}, "phone"),
        ({"given_name": "Ada", "organization": ""}, "organization"),
    ],
)
def test_google_contacts_arguments_are_bounded(arguments: dict[str, object], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        GoogleContactsOAuthAdapter._contact_payload(arguments)


@pytest.mark.parametrize("value", [0, 101, True])
def test_google_contacts_limit_is_bounded(value: object) -> None:
    with pytest.raises(ValueError, match="between 1 and 100"):
        GoogleContactsOAuthAdapter._limit({"limit": value})
