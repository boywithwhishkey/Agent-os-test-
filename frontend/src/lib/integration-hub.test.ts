import { describe, it, expect } from "vitest";
import {
  isConnected,
  isReadyToConnect,
  isComingSoon,
  statusBucket,
  bucketCounts,
  groupByCategory,
  primaryAction,
  matchesFilter,
} from "./integration-hub";
import type { UnifiedConnector } from "./integration-hub";

function connector(overrides: Partial<UnifiedConnector>): UnifiedConnector {
  return {
    id: "test",
    name: "Test Provider",
    description: "A test connector",
    category: "developer",
    connector_type: "api",
    icon: "Plug",
    auth_type: "api_key",
    capabilities: [],
    provider: "test",
    popular: false,
    documentation_url: null,
    implemented: true,
    requires: [],
    status: "needs_setup",
    configured: false,
    connected: null,
    last_check: null,
    last_check_latency_ms: null,
    last_check_error: null,
    last_execution: null,
    last_execution_success: null,
  capability_details: [],
  kind: "user_connector",
    ...overrides,
  };
}

describe("connector state classification", () => {
  it("a connector is CONNECTED only when implemented and status is literally connected", () => {
    const connected = connector({ status: "connected", configured: true });
    expect(isConnected(connected)).toBe(true);
    expect(isReadyToConnect(connected)).toBe(false);
    expect(isComingSoon(connected)).toBe(false);
  });

  it("setting credentials (configured=true) without a verified test is READY TO CONNECT, not CONNECTED", () => {
    // This is the exact bug this rule exists to prevent: `configured` only
    // means "credentials are present", not "a real connection succeeded".
    const configuredButUnverified = connector({ status: "configured", configured: true });
    expect(isConnected(configuredButUnverified)).toBe(false);
    expect(isReadyToConnect(configuredButUnverified)).toBe(true);
  });

  it("needs_setup and error are both READY TO CONNECT, never CONNECTED", () => {
    expect(isReadyToConnect(connector({ status: "needs_setup" }))).toBe(true);
    expect(isReadyToConnect(connector({ status: "error" }))).toBe(true);
    expect(isConnected(connector({ status: "error" }))).toBe(false);
  });

  it("a catalog-only (unimplemented) provider is always COMING SOON, regardless of status", () => {
    const catalogOnly = connector({ implemented: false, status: "available" });
    expect(isComingSoon(catalogOnly)).toBe(true);
    expect(isConnected(catalogOnly)).toBe(false);
    expect(isReadyToConnect(catalogOnly)).toBe(false);
  });

  it("the three states are always mutually exclusive", () => {
    const samples = [
      connector({ status: "connected" }),
      connector({ status: "configured" }),
      connector({ status: "needs_setup" }),
      connector({ status: "error" }),
      connector({ implemented: false, status: "available" }),
    ];
    for (const c of samples) {
      const flags = [isConnected(c), isReadyToConnect(c), isComingSoon(c)];
      expect(flags.filter(Boolean).length).toBe(1);
    }
  });
});

describe("primaryAction", () => {
  it("OAuth connectors awaiting authorization get a connect action, not a configure one", () => {
    // The distinction matters: an OAuth connector is not something an
    // operator fills in a form for, so it must never fall through to the
    // generic configure wording.
    const notion = connector({ name: "Notion", connector_type: "oauth", auth_type: "oauth2", status: "needs_setup" });
    expect(primaryAction(notion)).toEqual({ kind: "connect" });
  });

  it("non-OAuth connectors awaiting configuration get a configure action", () => {
    expect(primaryAction(connector({ connector_type: "webhook", status: "needs_setup" }))).toEqual({ kind: "configure" });
    expect(primaryAction(connector({ connector_type: "api", status: "needs_setup" }))).toEqual({ kind: "configure" });
  });

  it("a configured-but-unverified or errored connector gets a Test action", () => {
    expect(primaryAction(connector({ status: "configured" }))).toEqual({ kind: "test" });
    expect(primaryAction(connector({ status: "error" }))).toEqual({ kind: "test" });
  });

  it("a connected connector gets Manage, never a connect/configure CTA", () => {
    expect(primaryAction(connector({ status: "connected" }))).toEqual({ kind: "manage" });
  });

  it("a catalog-only provider gets coming_soon, never a working-looking CTA", () => {
    expect(primaryAction(connector({ implemented: false, status: "available" }))).toEqual({ kind: "coming_soon" });
  });
});

describe("matchesFilter", () => {
  it("supports filtering by each of the three states", () => {
    const connectedC = connector({ status: "connected" });
    const readyC = connector({ status: "needs_setup" });
    const comingSoonC = connector({ implemented: false, status: "available" });

    expect(matchesFilter(connectedC, "connected")).toBe(true);
    expect(matchesFilter(readyC, "connected")).toBe(false);

    expect(matchesFilter(readyC, "ready")).toBe(true);
    expect(matchesFilter(connectedC, "ready")).toBe(false);

    expect(matchesFilter(comingSoonC, "coming_soon")).toBe(true);
    expect(matchesFilter(readyC, "coming_soon")).toBe(false);
  });

  it("supports filtering by connector_type including oauth and webhook", () => {
    expect(matchesFilter(connector({ connector_type: "oauth" }), "oauth")).toBe(true);
    expect(matchesFilter(connector({ connector_type: "webhook" }), "webhook")).toBe(true);
    expect(matchesFilter(connector({ connector_type: "oauth" }), "webhook")).toBe(false);
  });
});

describe("statusBucket", () => {
  it("treats `available` as NOT BUILT, never as ready to use", () => {
    // The single most consequential mapping on the marketplace: the backend
    // reserves `available` for catalog-only entries with no adapter behind
    // them. Reading it as "available to use" would advertise software that
    // does not exist.
    expect(statusBucket(connector({ implemented: false, status: "available" }))).toBe("not_built");
  });

  it("keeps `configured` out of the connected bucket", () => {
    // Credentials being present is not proof they work.
    expect(statusBucket(connector({ status: "configured", configured: true }))).toBe("needs_verification");
    expect(statusBucket(connector({ status: "error" }))).toBe("needs_verification");
    expect(statusBucket(connector({ status: "connected" }))).toBe("connected");
  });

  it("puts a built connector awaiting credentials in needs_setup", () => {
    expect(statusBucket(connector({ status: "needs_setup" }))).toBe("needs_setup");
    expect(statusBucket(connector({ status: "disabled" }))).toBe("needs_setup");
  });

  it("assigns every connector to exactly one bucket", () => {
    const all = (["connected", "configured", "needs_setup", "available", "error", "disabled"] as const).map((status) =>
      connector({ status, implemented: status !== "available" })
    );
    const counts = bucketCounts(all);
    expect(Object.values(counts).reduce((a, b) => a + b, 0)).toBe(all.length);
  });
});

describe("groupByCategory", () => {
  it("orders groups by CATEGORY_ORDER and drops empty ones", () => {
    const groups = groupByCategory([
      connector({ id: "d", category: "data" }),
      connector({ id: "a", category: "ai" }),
    ]);
    expect(groups.map((g) => g.category)).toEqual(["ai", "data"]);
  });

  it("never opens a group with something nobody can use", () => {
    // A not-built entry must not lead its category just because it sorts
    // first alphabetically — the first card in a group sets the expectation
    // for the whole group.
    const groups = groupByCategory([
      connector({ id: "aaa", name: "Aaa", category: "ai", implemented: false, status: "available" }),
      connector({ id: "zzz", name: "Zzz", category: "ai", status: "needs_setup" }),
    ]);
    expect(groups[0].connectors[0].id).toBe("zzz");
  });

  it("puts popular working connectors ahead of the rest within a group", () => {
    const groups = groupByCategory([
      connector({ id: "plain", name: "Plain", category: "ai", status: "needs_setup" }),
      connector({ id: "star", name: "Star", category: "ai", status: "needs_setup", popular: true }),
    ]);
    expect(groups[0].connectors.map((c) => c.id)).toEqual(["star", "plain"]);
  });
});
