import type { ConnectorEntry, MCPServer } from "./types";

export interface UnifiedConnector extends ConnectorEntry {
  /** Present only when this entry is a user-configured MCP server, not a
   * static catalog entry — lets the UI enable Test/Disconnect actions. */
  mcpServer?: MCPServer;
}

export function mcpServerToConnector(server: MCPServer): UnifiedConnector {
  const caps = server.capabilities;
  const capabilities = caps
    ? [...caps.tools.map((t) => t.name), ...caps.resources.map((r) => r.name), ...caps.prompts.map((p) => p.name)]
    : [];
  const status: UnifiedConnector["status"] = !server.enabled
    ? "disabled"
    : server.connected === true
      ? "connected"
      : server.connected === false
        ? "error"
        : "configured";

  return {
    id: `mcp:${server.id}`,
    name: server.name,
    description: `MCP server at ${server.endpoint}`,
    category: "other",
    connector_type: "mcp",
    icon: "Plug",
    auth_type: server.auth_type === "none" ? "none" : "bearer",
    capabilities,
    provider: server.id,
    popular: false,
    documentation_url: null,
    implemented: true,
    requires: [],
    status,
    configured: true,
    connected: server.connected,
    last_check: server.last_check,
    last_check_latency_ms: server.last_check_latency_ms,
    last_check_error: server.last_check_error,
    last_execution: null,
    last_execution_success: null,
    mcpServer: server,
  };
}

export function isCurrentlyIntegrated(connector: UnifiedConnector): boolean {
  return connector.implemented && connector.configured;
}

export function matchesSearch(connector: UnifiedConnector, query: string): boolean {
  if (!query.trim()) return true;
  const haystack = [
    connector.name,
    connector.description,
    connector.category,
    connector.connector_type,
    ...connector.capabilities,
  ]
    .join(" ")
    .toLowerCase();
  return haystack.includes(query.trim().toLowerCase());
}

export type FilterChip = "all" | "connected" | "mcp" | "api" | "automation" | "ai" | "productivity" | "developer" | "data";

export function matchesFilter(connector: UnifiedConnector, filter: FilterChip): boolean {
  switch (filter) {
    case "all":
      return true;
    case "connected":
      return isCurrentlyIntegrated(connector);
    case "mcp":
    case "api":
      return connector.connector_type === filter;
    default:
      return connector.category === filter;
  }
}
