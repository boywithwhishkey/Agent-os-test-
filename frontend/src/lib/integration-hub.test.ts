import { describe, it, expect } from "vitest";
import {
  isConnected,
  isReadyToConnect,
  isComingSoon,
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
  it("OAuth connectors awaiting authorization get a 'Connect <Provider>' CTA, never generic API-key wording", () => {
    const notion = connector({ name: "Notion", connector_type: "oauth", auth_type: "oauth2", status: "needs_setup" });
    const action = primaryAction(notion);
    expect(action).toEqual({ kind: "connect", label: "Connect Notion" });
  });

  it("webhook connectors awaiting configuration get 'Configure webhook'", () => {
    const action = primaryAction(connector({ connector_type: "webhook", status: "needs_setup" }));
    expect(action).toEqual({ kind: "configure", label: "Configure webhook" });
  });

  it("API-key connectors awaiting configuration get plain 'Configure'", () => {
    const action = primaryAction(connector({ connector_type: "api", status: "needs_setup" }));
    expect(action).toEqual({ kind: "configure", label: "Configure" });
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
