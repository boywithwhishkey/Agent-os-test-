from __future__ import annotations

import json

import httpx
import pytest

from app.integrations.dropbox import DropboxOAuthAdapter
from app.integrations.oauth.store import OAuthConnectionStore
from app.integrations.onedrive import OneDriveOAuthAdapter


def _store(provider: str) -> OAuthConnectionStore:
    store = OAuthConnectionStore()
    store.record_success(provider, access_token=f"{provider}-access-token", token_type="Bearer", scope="read")
    return store


@pytest.mark.anyio
async def test_dropbox_identity_and_file_list_use_fixed_rpc_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.url.path, request.headers["authorization"]))
        if request.url.path.endswith("get_current_account"):
            return httpx.Response(200, json={"account_id": "dbid:1"})
        return httpx.Response(200, json={"entries": [{"name": "report.pdf"}], "has_more": False})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = DropboxOAuthAdapter(connection_store=_store("dropbox"), client=client)
        identity = await adapter.run_capability("identity.account.read", {})
        files = await adapter.run_capability("files.file.list", {"max_results": 5})
    finally:
        await client.aclose()

    assert identity["account_id"] == "dbid:1"
    assert files["entries"][0]["name"] == "report.pdf"
    assert seen == [
        ("/2/users/get_current_account", "Bearer dropbox-access-token"),
        ("/2/files/list_folder", "Bearer dropbox-access-token"),
    ]


@pytest.mark.anyio
async def test_onedrive_identity_and_root_list_use_graph_read_calls() -> None:
    seen: list[tuple[str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.url.path, request.url.query.decode()))
        if request.url.path == "/v1.0/me":
            return httpx.Response(200, json={"id": "user-1", "displayName": "Demo"})
        return httpx.Response(200, json={"value": [{"id": "file-1", "name": "notes.txt"}]})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        adapter = OneDriveOAuthAdapter(connection_store=_store("onedrive"), client=client)
        identity = await adapter.run_capability("identity.account.read", {})
        files = await adapter.run_capability("files.file.list", {"max_results": 10})
    finally:
        await client.aclose()

    assert identity["id"] == "user-1"
    assert files["value"][0]["name"] == "notes.txt"
    assert seen == [
        ("/v1.0/me", "%24select=id%2CdisplayName%2CuserPrincipalName"),
        (
            "/v1.0/me/drive/root/children",
            "%24top=10&%24select=id%2Cname%2Csize%2Cfile%2Cfolder%2ClastModifiedDateTime",
        ),
    ]


@pytest.mark.anyio
async def test_dropbox_file_write_uses_content_upload_endpoint() -> None:
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["auth"] = request.headers["authorization"]
        seen["arg"] = json.loads(request.headers["dropbox-api-arg"])
        seen["content_type"] = request.headers["content-type"]
        seen["body"] = request.content
        return httpx.Response(200, json={"name": "notes.txt", "path_display": "/notes.txt"})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await DropboxOAuthAdapter(connection_store=_store("dropbox"), client=client).run_capability(
            "files.file.write",
            {"path": "/notes.txt", "content": "hello dropbox", "mode": "overwrite"},
        )
    finally:
        await client.aclose()

    assert result["path_display"] == "/notes.txt"
    assert seen == {
        "path": "/2/files/upload",
        "auth": "Bearer dropbox-access-token",
        "arg": {"path": "/notes.txt", "mode": "overwrite", "autorename": False, "mute": False},
        "content_type": "application/octet-stream",
        "body": b"hello dropbox",
    }


@pytest.mark.anyio
async def test_dropbox_file_delete_uses_governed_rpc_endpoint() -> None:
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["path"] = request.url.path
        seen["auth"] = request.headers["authorization"]
        seen["body"] = json.loads(request.content)
        return httpx.Response(200, json={"metadata": {"name": "notes.txt", ".tag": "file"}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await DropboxOAuthAdapter(connection_store=_store("dropbox"), client=client).run_capability(
            "files.file.delete", {"path": "/notes.txt"}
        )
    finally:
        await client.aclose()

    assert result == {
        "provider": "dropbox",
        "path": "/notes.txt",
        "deleted": True,
        "metadata": {"name": "notes.txt", ".tag": "file"},
    }
    assert seen == {
        "path": "/2/files/delete_v2",
        "auth": "Bearer dropbox-access-token",
        "body": {"path": "/notes.txt"},
    }


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"path": "relative.txt", "content": "x"}, "absolute"),
        ({"path": "/../bad", "content": "x"}, "safe"),
        ({"path": "/x.txt", "content": "", "mode": "add"}, "text content"),
        ({"path": "/x.txt", "content": "x", "mode": "bad"}, "mode"),
    ],
)
def test_dropbox_file_arguments_are_validated(
    arguments: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        DropboxOAuthAdapter._file_payload(arguments)


def test_dropbox_delete_path_is_validated() -> None:
    with pytest.raises(ValueError, match="safe absolute"):
        DropboxOAuthAdapter._path_argument({"path": "/../bad"}, operation="files.file.delete")


@pytest.mark.anyio
async def test_onedrive_file_write_uses_graph_content_endpoint() -> None:
    seen: dict[str, object] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        seen["method"] = request.method
        seen["path"] = request.url.path
        seen["auth"] = request.headers["authorization"]
        seen["content_type"] = request.headers["content-type"]
        seen["body"] = request.content
        return httpx.Response(201, json={"id": "file-2", "name": "notes.txt", "size": 12})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    try:
        result = await OneDriveOAuthAdapter(connection_store=_store("onedrive"), client=client).run_capability(
            "files.file.write",
            {"path": "/Documents/notes.txt", "content": "hello onedrive", "mime_type": "text/plain"},
        )
    finally:
        await client.aclose()

    assert result["id"] == "file-2"
    assert seen == {
        "method": "PUT",
        "path": "/v1.0/me/drive/root:/Documents/notes.txt:/content",
        "auth": "Bearer onedrive-access-token",
        "content_type": "text/plain",
        "body": b"hello onedrive",
    }


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        ({"path": "relative.txt", "content": "x"}, "absolute"),
        ({"path": "/../bad", "content": "x"}, "safe"),
        ({"path": "/x.txt", "content": "", "mime_type": "text/plain"}, "text content"),
        ({"path": "/x.txt", "content": "x", "mime_type": "bad"}, "MIME"),
    ],
)
def test_onedrive_file_arguments_are_validated(
    arguments: dict[str, object], message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        OneDriveOAuthAdapter._file_payload(arguments)


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("adapter", "message"),
    [
        (DropboxOAuthAdapter(connection_store=OAuthConnectionStore()), "Dropbox"),
        (OneDriveOAuthAdapter(connection_store=OAuthConnectionStore()), "OneDrive"),
    ],
)
async def test_file_connectors_report_missing_oauth_connection(adapter, message: str) -> None:
    connected, latency_ms, error = await adapter.test_connection()
    assert connected is False
    assert latency_ms is not None
    assert error == f"Not authorized yet — use Authorize to connect a {message} account."
