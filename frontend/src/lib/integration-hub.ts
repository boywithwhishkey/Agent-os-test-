import type { ConnectorCategory, ConnectorEntry, MCPServer } from "./types";

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
    // Deliberately empty. A discovered MCP tool has no canonical capability
    // mapping, and deriving one from the server's own tool names would let a
    // remote server choose its own risk level — the exact thing "unknown MCP
    // tool, deny by default" exists to prevent. The discovered tool names are
    // still listed above as untrusted display text.
    capability_details: [],
    kind: "user_connector",
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
  | { kind: "connect" }
  | { kind: "configure" }
  | { kind: "test" }
  | { kind: "coming_soon" };

/**
 * The one primary call-to-action for a connector card/drawer, driven by its
 * real connector_type and live status — never a working-looking CTA for a
 * Coming Soon connector, and never generic "Configure" wording where the real
 * action is an OAuth handshake.
 *
 * Returns the KIND only. Wording lives in the locale catalogue, so this stays
 * the single place that decides what the action IS while the UI decides what
 * it is called.
 */
export function primaryAction(connector: UnifiedConnector): PrimaryAction {
  if (isComingSoon(connector)) return { kind: "coming_soon" };
  if (connector.status === "connected") return { kind: "manage" };
  if (connector.mcpServer) return { kind: "test" };
  if (connector.status === "configured" || connector.status === "error") return { kind: "test" };

  // needs_setup: the connector has no credentials/authorization yet.
  return connector.connector_type === "oauth" ? { kind: "connect" } : { kind: "configure" };
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
  | "data"
  | "google";

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

/**
 * Marketplace grouping.
 *
 * These four buckets are derived from what the backend actually reports, not
 * from a tidier taxonomy someone would prefer. Two things about the real data
 * shape the result and are easy to get wrong:
 *
 * - `available` does NOT mean "ready to use". `ConnectorEntry` reserves it for
 *   catalog-only entries with no adapter behind them (see
 *   app/integrations/models.py), so it maps to NOT BUILT YET. A marketplace
 *   that showed those under "Available" would be advertising software that
 *   does not exist.
 * - `configured` is not `connected`. Credentials being present is not proof
 *   they work, so it gets its own bucket — the operator's next action there is
 *   to verify, not to enter anything.
 */
export type StatusBucket = "connected" | "needs_verification" | "needs_setup" | "not_built";

export const STATUS_BUCKETS: StatusBucket[] = [
  "connected",
  "needs_verification",
  "needs_setup",
  "not_built",
];

export function statusBucket(connector: UnifiedConnector): StatusBucket {
  if (!connector.implemented) return "not_built";
  if (connector.status === "connected") return "connected";
  if (connector.status === "configured" || connector.status === "error") return "needs_verification";
  return "needs_setup";
}

/** Category browse order — most-used first, `other` last, so the marketplace
 * opens on the things operators actually reach for. */
export const CATEGORY_ORDER: ConnectorCategory[] = [
  "ai",
  "automation",
  "productivity",
  "google",
  "developer",
  "data",
  "other",
];

export interface CategoryGroup {
  category: ConnectorCategory;
  connectors: UnifiedConnector[];
}

/**
 * Groups connectors by category in CATEGORY_ORDER, dropping empty groups.
 * Within a group, working connectors come before not-built ones and popular
 * before the rest — so a group never opens with something nobody can use.
 */
export function groupByCategory(connectors: UnifiedConnector[]): CategoryGroup[] {
  const rank = (c: UnifiedConnector) => (isComingSoon(c) ? 2 : 0) + (c.popular ? 0 : 1);
  return CATEGORY_ORDER.map((category) => ({
    category,
    connectors: connectors
      .filter((c) => c.category === category)
      .sort((a, b) => rank(a) - rank(b) || a.name.localeCompare(b.name)),
  })).filter((group) => group.connectors.length > 0);
}

/** How many connectors sit in each bucket — for the filter chips, so an
 * operator can see what a filter holds before spending a tap on it. */
export function bucketCounts(connectors: UnifiedConnector[]): Record<StatusBucket, number> {
  const counts: Record<StatusBucket, number> = {
    connected: 0,
    needs_verification: 0,
    needs_setup: 0,
    not_built: 0,
  };
  for (const c of connectors) counts[statusBucket(c)] += 1;
  return counts;
}

/**
 * THYNACT's own persistence and queue are not services anyone connects an
 * account to. They stay visible for diagnostics but are counted and grouped
 * separately, so the marketplace's numbers describe connectors a user can
 * actually act on rather than being padded by the running system.
 */
export function isSystemInfrastructure(connector: UnifiedConnector): boolean {
  return connector.kind === "system_infrastructure";
}

export function isUserConnector(connector: UnifiedConnector): boolean {
  return !isSystemInfrastructure(connector);
}
