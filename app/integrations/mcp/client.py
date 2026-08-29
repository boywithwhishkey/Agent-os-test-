from __future__ import annotations

import json
import time

import httpx

from app.integrations.mcp.models import MCPAuthType, MCPCapabilities, MCPCapabilityItem

MCP_PROTOCOL_VERSION = "2025-03-26"


class MCPClientError(Exception):
    """A well-formed JSON-RPC error response from the MCP server."""


class MCPHttpClient:
    """Minimal MCP client for the remote "Streamable HTTP" transport.

    Sends JSON-RPC 2.0 requests over a single HTTP POST per call. Handles a
    plain JSON response or a single-event text/event-stream response (the
    two shapes a Streamable HTTP server can reply with to a client request).
    Does not implement server-initiated streaming/notifications — this is a
    discovery/health client, not a full MCP session manager.
    """

    def __init__(
        self,
        *,
        endpoint: str,
        auth_type: MCPAuthType = MCPAuthType.NONE,
        header_name: str | None = None,
        secret_value: str | None = None,
        timeout_seconds: float = 15.0,
        client: httpx.AsyncClient | None = None,
    ) -> None:
        self.endpoint = endpoint
        self.auth_type = auth_type
        self.header_name = header_name
        self.secret_value = secret_value
        self.timeout_seconds = timeout_seconds
        self._client = client

    def _headers(self) -> dict[str, str]:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        if self.auth_type == MCPAuthType.BEARER and self.secret_value:
            headers["Authorization"] = f"Bearer {self.secret_value}"
        elif self.auth_type == MCPAuthType.HEADER and self.header_name and self.secret_value:
            headers[self.header_name] = self.secret_value
        return headers

    @staticmethod
    def _parse_body(response: httpx.Response) -> dict:
        content_type = response.headers.get("content-type", "")
        if "text/event-stream" in content_type:
            for line in response.text.splitlines():
                if line.startswith("data:"):
                    return json.loads(line[len("data:") :].strip())
            raise MCPClientError("Empty event-stream response from MCP server")
        return response.json()

    async def _call(self, client: httpx.AsyncClient, method: str, params: dict | None = None) -> dict:
        body = {"jsonrpc": "2.0", "id": 1, "method": method, "params": params or {}}
        response = await client.post(
            self.endpoint, json=body, headers=self._headers(), timeout=self.timeout_seconds
        )
        response.raise_for_status()
        payload = self._parse_body(response)
        if "error" in payload:
            message = payload["error"].get("message", "MCP server returned an error")
            raise MCPClientError(message)
        return payload.get("result", {})

    async def _list_capability(self, client: httpx.AsyncClient, method: str, key: str) -> list[MCPCapabilityItem]:
        try:
            result = await self._call(client, method)
        except MCPClientError:
            # The server may simply not implement this optional capability —
            # that isn't a connection failure.
            return []
        items = result.get(key, [])
        return [
            MCPCapabilityItem(name=item.get("name", "unknown"), description=item.get("description"))
            for item in items
            if isinstance(item, dict)
        ]

    async def discover(self) -> tuple[bool, float | None, str | None, MCPCapabilities]:
        """Initialize the session and enumerate tools/resources/prompts.

        Returns (connected, latency_ms, error, capabilities). Never raises —
        every failure mode is captured in the return value for the caller to
        record and display honestly.
        """
        own_client = self._client is None
        client = self._client or httpx.AsyncClient()
        started = time.perf_counter()
        try:
            await self._call(
                client,
                "initialize",
                {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "thynact", "version": "0.1.0"},
                },
            )
            tools = await self._list_capability(client, "tools/list", "tools")
            resources = await self._list_capability(client, "resources/list", "resources")
            prompts = await self._list_capability(client, "prompts/list", "prompts")
            latency_ms = (time.perf_counter() - started) * 1000
            return True, latency_ms, None, MCPCapabilities(tools=tools, resources=resources, prompts=prompts)
        except httpx.TimeoutException:
            return False, None, "Connection to MCP server timed out", MCPCapabilities()
        except httpx.HTTPStatusError as exc:
            return False, None, f"MCP server returned HTTP {exc.response.status_code}", MCPCapabilities()
        except httpx.HTTPError as exc:
            return False, None, f"{type(exc).__name__}: {exc}", MCPCapabilities()
        except MCPClientError as exc:
            return False, None, str(exc), MCPCapabilities()
        finally:
            if own_client:
                await client.aclose()
