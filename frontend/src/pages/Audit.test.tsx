import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { renderWithProviders } from "@/test/utils";
import { setApiKey, resetApiConfig } from "@/lib/api/config";
import Audit from "./Audit";

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const withCorrelation = {
  timestamp: "2026-08-31T09:26:05.169347+00:00",
  tool: "echo",
  success: true,
  risk: "read",
  approval_required: false,
  error: null,
  correlation_id: "bootstrap-trace-001",
};

// Events recorded before migration 006 have no correlation id at all; the UI
// must not render an empty "Correlation ID" block for them.
const withoutCorrelation = { ...withCorrelation, tool: "json.validate", correlation_id: null };

beforeEach(() => {
  setApiKey("test-key");
});

afterEach(() => {
  cleanup();
  resetApiConfig();
  vi.unstubAllGlobals();
});

describe("Audit", () => {
  it("shows the correlation id with a copy control", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse([withCorrelation])));
    const writeText = vi.fn(async () => {});
    vi.stubGlobal("navigator", { ...navigator, clipboard: { writeText } });

    renderWithProviders(<Audit />);

    // Mobile cards and the desktop table both render (CSS decides which is
    // visible), so target the first match rather than asserting uniqueness.
    await screen.findAllByText("echo");
    fireEvent.click(screen.getAllByText("echo")[0]);

    await waitFor(() => expect(screen.getByText("Correlation ID")).toBeInTheDocument());
    expect(screen.getByText("bootstrap-trace-001")).toBeInTheDocument();

    fireEvent.click(screen.getByLabelText("Copy correlation ID"));
    expect(writeText).toHaveBeenCalledWith("bootstrap-trace-001");
  });

  it("omits the correlation block when the event has none", async () => {
    vi.stubGlobal("fetch", vi.fn(async () => jsonResponse([withoutCorrelation])));

    renderWithProviders(<Audit />);

    await screen.findAllByText("json.validate");
    fireEvent.click(screen.getAllByText("json.validate")[0]);

    await waitFor(() => expect(screen.getAllByText("json.validate").length).toBeGreaterThan(0));
    expect(screen.queryByText("Correlation ID")).not.toBeInTheDocument();
  });
});
