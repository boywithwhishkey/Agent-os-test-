import { describe, it, expect, vi, afterEach, beforeEach } from "vitest";
import { render, screen, cleanup, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

function mockBackend() {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockImplementation(async (url: string) => {
      const json = (body: unknown, status = 200) =>
        new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json" } });
      if (url.endsWith("/health")) return json({ status: "ok", service: "THYNACT", environment: "test" });
      if (url.endsWith("/ready")) return json({ status: "ready", checks: {} });
      if (url.endsWith("/api/v1/tools/audit")) return json([]);
      if (url.endsWith("/api/v1/tools")) return json([]);
      return json({});
    })
  );
}

describe("App shell", () => {
  beforeEach(() => {
    vi.resetModules();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    cleanup();
  });

  it("renders the navigation and the dashboard by default", async () => {
    mockBackend();
    const { App } = await import("./App");
    render(<App />);

    const nav = await screen.findByRole("navigation");
    expect(within(nav).getByText("Dashboard")).toBeInTheDocument();
    expect(within(nav).getByText("Tasks")).toBeInTheDocument();
    expect(within(nav).getByText("Orchestrate")).toBeInTheDocument();
    // API reachability moved out of the header and into the account popover,
    // so it has to be opened. Same intent as before: the shell reports the
    // backend as reachable.
    await userEvent.click(screen.getByRole("button", { name: /account and operator session/i }));
    await waitFor(() => expect(screen.getByText("API online")).toBeInTheDocument());
  });

  it("navigates to the Tasks screen when its nav link is clicked", async () => {
    mockBackend();
    const { App } = await import("./App");
    const user = userEvent.setup();

    render(<App />);
    const nav = await screen.findByRole("navigation");
    await user.click(within(nav).getByRole("link", { name: /tasks/i }));

    expect(await screen.findByRole("heading", { name: "Tasks" })).toBeInTheDocument();
  });
});
