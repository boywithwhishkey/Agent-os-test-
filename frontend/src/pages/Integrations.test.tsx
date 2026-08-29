import { describe, it, expect, vi, afterEach } from "vitest";
import { screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { renderWithProviders } from "@/test/utils";
import Integrations from "./Integrations";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

describe("Integrations page", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    cleanup();
  });

  it("shows an unconfigured connector with its required setup", async () => {
    const fetchMock = vi.fn().mockImplementation(async () =>
      jsonResponse([
        {
          provider: "n8n",
          name: "n8n",
          configured: false,
          requires: ["N8N_BASE_URL"],
          connected: null,
          last_check: null,
          last_check_latency_ms: null,
          last_check_error: null,
          last_execution: null,
          last_execution_success: null,
        },
      ])
    );
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<Integrations />);

    expect(await screen.findByText(/unconfigured/i)).toBeInTheDocument();
    expect(screen.getByText("N8N_BASE_URL")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /test connection/i })).toBeDisabled();
  });

  it("runs a connection test for a configured connector", async () => {
    const listBody = {
      provider: "n8n",
      name: "n8n",
      configured: true,
      requires: ["N8N_BASE_URL"],
      connected: null,
      last_check: null,
      last_check_latency_ms: null,
      last_check_error: null,
      last_execution: null,
      last_execution_success: null,
    };
    const testedBody = { ...listBody, connected: true, last_check: new Date().toISOString(), last_check_latency_ms: 12.3 };

    const fetchMock = vi.fn().mockImplementation(async (url: string, init?: RequestInit) => {
      if (init?.method === "POST" && String(url).endsWith("/n8n/test")) {
        return jsonResponse(testedBody);
      }
      return jsonResponse([listBody]);
    });
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<Integrations />);

    const testButton = await screen.findByRole("button", { name: /test connection/i });
    expect(testButton).toBeEnabled();
    fireEvent.click(testButton);

    await waitFor(() => expect(screen.getAllByText(/healthy/i).length).toBeGreaterThan(0));
    expect(screen.getByText("12 ms")).toBeInTheDocument();
  });
});
