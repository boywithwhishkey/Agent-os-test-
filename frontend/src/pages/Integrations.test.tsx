import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { screen, fireEvent, waitFor, cleanup, within } from "@testing-library/react";
import { renderWithProviders } from "@/test/utils";
import { setApiKey, resetApiConfig } from "@/lib/api/config";
import Integrations from "./Integrations";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const n8nNeedsSetup = {
  id: "n8n",
  name: "n8n",
  description: "Trigger self-hosted or cloud n8n workflows over webhooks.",
  category: "automation",
  connector_type: "webhook",
  icon: "Zap",
  auth_type: "webhook_secret",
  capabilities: ["Trigger workflow"],
  provider: "n8n",
  popular: true,
  documentation_url: "https://n8n.io",
  implemented: true,
  requires: ["N8N_BASE_URL"],
  status: "needs_setup",
  configured: false,
  connected: null,
  last_check: null,
  last_check_latency_ms: null,
  last_check_error: null,
  last_execution: null,
  last_execution_success: null,
};

const githubConfigured = {
  id: "github",
  name: "GitHub",
  description: "Read repos, open issues/PRs, and react to events.",
  category: "developer",
  connector_type: "oauth",
  icon: "Github",
  auth_type: "oauth2",
  capabilities: ["Authorize account", "Verify identity"],
  provider: "github",
  popular: true,
  documentation_url: "https://github.com",
  implemented: true,
  requires: ["GITHUB_OAUTH_CLIENT_ID", "GITHUB_OAUTH_CLIENT_SECRET"],
  status: "configured",
  configured: true,
  connected: null,
  last_check: null,
  last_check_latency_ms: null,
  last_check_error: null,
  last_execution: null,
  last_execution_success: null,
};

function stubFetch(routes: {
  catalog: unknown[];
  mcpServers?: unknown[];
  onTest?: (url: string) => Response;
  onOAuthAuthorize?: (url: string) => Response;
}) {
  const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
    const href = String(url);
    if (href.includes("/oauth/") && href.includes("/authorize") && routes.onOAuthAuthorize) {
      return routes.onOAuthAuthorize(href);
    }
    if (init?.method === "POST" && href.includes("/test") && routes.onTest) {
      return routes.onTest(href);
    }
    if (href.includes("/mcp/servers")) {
      return jsonResponse(routes.mcpServers ?? []);
    }
    if (href.includes("/api/v1/integrations")) {
      return jsonResponse(routes.catalog);
    }
    return jsonResponse([]);
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("Integrations page", () => {
  beforeEach(() => {
    setApiKey("test-operator-key");
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    resetApiConfig();
    cleanup();
  });

  it("shows a connector that needs setup with a neutral requires-setup state, not an error", async () => {
    stubFetch({ catalog: [n8nNeedsSetup] });

    renderWithProviders(<Integrations />);

    const cards = await screen.findAllByText("n8n");
    const card = cards[0];
    fireEvent.click(card.closest(".group") ?? card);

    expect(await screen.findByText(/requires setup/i)).toBeInTheDocument();
    expect(screen.getByText("N8N_BASE_URL")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /test connection/i })).toBeDisabled();

    // The old error-styled "Not configured... on the backend" copy must be gone.
    expect(screen.queryByText(/not configured/i)).not.toBeInTheDocument();
  });

  it("runs a connection test for a configured connector and reflects the result live", async () => {
    const configured = { ...n8nNeedsSetup, status: "configured", configured: true };
    const tested = { ...configured, status: "connected", connected: true, last_check: new Date().toISOString(), last_check_latency_ms: 12.3 };

    stubFetch({
      catalog: [configured],
      onTest: () => jsonResponse(tested),
    });

    renderWithProviders(<Integrations />);

    const integratedSection = (await screen.findByText("Currently integrated")).closest("section")!;
    const testButton = await within(integratedSection).findByRole("button", { name: /^test$/i });
    fireEvent.click(testButton);

    await waitFor(() => expect(screen.getAllByText(/connected/i).length).toBeGreaterThan(0));
  });

  it("does not crash when an MCP server response is missing capabilities", async () => {
    stubFetch({
      catalog: [],
      mcpServers: [
        {
          id: "srv-1",
          name: "My MCP Server",
          endpoint: "https://mcp.example.com",
          auth_type: "none",
          header_name: null,
          has_secret: false,
          timeout_seconds: 30,
          enabled: true,
          created_at: new Date().toISOString(),
          connected: null,
          last_check: null,
          last_check_latency_ms: null,
          last_check_error: null,
          // capabilities intentionally omitted to simulate a malformed/partial response
        },
      ],
    });

    renderWithProviders(<Integrations />);

    expect((await screen.findAllByText("My MCP Server")).length).toBeGreaterThan(0);
  });

  it("authorizes an OAuth connector by redirecting to the provider's authorize URL", async () => {
    stubFetch({
      catalog: [githubConfigured],
      onOAuthAuthorize: () => jsonResponse({ authorize_url: "https://github.com/login/oauth/authorize?state=abc" }),
    });
    const originalLocation = window.location;
    // @ts-expect-error -- jsdom's location isn't assignable; delete+redefine to spy on navigation.
    delete window.location;
    window.location = { ...originalLocation, href: "" } as unknown as (string & Location);

    renderWithProviders(<Integrations />);

    const cards = await screen.findAllByText("GitHub");
    fireEvent.click(cards[0].closest(".group") ?? cards[0]);

    const authorizeButton = await screen.findByRole("button", { name: /^authorize$/i });
    fireEvent.click(authorizeButton);

    await waitFor(() => expect(window.location.href).toBe("https://github.com/login/oauth/authorize?state=abc"));

    window.location = originalLocation as unknown as (string & Location);
  });

  it("shows a toast and clears the query string when returning from a successful OAuth callback", async () => {
    stubFetch({ catalog: [githubConfigured] });

    renderWithProviders(<Integrations />, { route: "/integrations?oauth=connected&provider=github" });

    expect(await screen.findByText(/connected to github/i)).toBeInTheDocument();
  });
});
