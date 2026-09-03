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

  it("gives the dashboard a first move and a way into the rest of the product", async () => {
    // The dashboard used to be the brand mark, four metrics and half a screen
    // of empty canvas. These are the additions that fill it; if one is dropped
    // the home screen goes back to having no obvious next step.
    // jsdom's URL persists between tests and the previous one navigates away.
    window.history.pushState({}, "", "/");
    mockBackend();
    const { App } = await import("./App");
    render(<App />);

    // Two now point there — the hero call to action and the quick action.
    const starts = await screen.findAllByRole("link", { name: /start orchestration/i });
    expect(starts.length).toBeGreaterThanOrEqual(2);
    expect(starts.every((l) => l.getAttribute("href") === "/orchestrate")).toBe(true);

    for (const [name, href] of [
      [/product overview/i, "/overview"],
      [/connectors/i, "/integrations"],
      [/about thynact/i, "/about"],
      [/system health/i, "/system-health"],
    ] as const) {
      const links = await screen.findAllByRole("link", { name });
      expect(links.some((l) => l.getAttribute("href") === href)).toBe(true);
    }
  });
});
