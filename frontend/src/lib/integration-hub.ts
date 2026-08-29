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

/**
 * A connector shown in the Integration Hub is always exactly one of three
 * states — never a blend of them (see CLAUDE.md's Integration Hub product
 * rule): CONNECTED (a real, verified connection), READY TO CONNECT
 * (implementation-complete, only credentials/OAuth are missing), or COMING
 * SOON (no adapter exists yet — catalog metadata only).
 */
export function isConnected(connector: UnifiedConnector): boolean {
  return connector.implemented && connector.status === "connected";
}

export function isReadyToConnect(connector: UnifiedConnector): boolean {
  return connector.implemented && connector.status !== "connected";
}

export function isComingSoon(connector: UnifiedConnector): boolean {
  return !connector.implemented;
}

export type PrimaryAction =
  | { kind: "manage" }
  | { kind: "connect"; label: string }
  | { kind: "configure"; label: string }
  | { kind: "test" }
  | { kind: "coming_soon" };

/** The one primary call-to-action for a connector card/drawer, driven by
 * its real connector_type and live status — never generic "Configure"
 * wording for an OAuth connector, and never a working-looking CTA for a
 * Coming Soon one. */
export function primaryAction(connector: UnifiedConnector): PrimaryAction {
  if (isComingSoon(connector)) return { kind: "coming_soon" };
  if (connector.status === "connected") return { kind: "manage" };
  if (connector.mcpServer) return { kind: "test" };
  if (connector.status === "configured" || connector.status === "error") return { kind: "test" };

  // needs_setup: the connector has no credentials/authorization yet.
  switch (connector.connector_type) {
    case "oauth":
      return { kind: "connect", label: `Connect ${connector.name}` };
    case "webhook":
      return { kind: "configure", label: "Configure webhook" };
    default:
      return { kind: "configure", label: "Configure" };
  }
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

export type FilterChip =
  | "all"
  | "connected"
  | "ready"
  | "coming_soon"
  | "mcp"
  | "api"
  | "oauth"
  | "webhook"
  | "automation"
  | "ai"
  | "productivity"
  | "developer"
  | "data";

export function matchesFilter(connector: UnifiedConnector, filter: FilterChip): boolean {
  switch (filter) {
    case "all":
      return true;
    case "connected":
      return isConnected(connector);
    case "ready":
      return isReadyToConnect(connector);
    case "coming_soon":
      return isComingSoon(connector);
    case "mcp":
    case "api":
    case "oauth":
    case "webhook":
      return connector.connector_type === filter;
    default:
      return connector.category === filter;
  }
}
