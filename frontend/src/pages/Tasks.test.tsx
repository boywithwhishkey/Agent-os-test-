import { describe, it, expect, vi, afterEach } from "vitest";
import { screen, fireEvent, waitFor, cleanup } from "@testing-library/react";
import { renderWithProviders } from "@/test/utils";
import Tasks from "./Tasks";

describe("Tasks page", () => {
  afterEach(() => {
    vi.restoreAllMocks();
    vi.unstubAllGlobals();
    cleanup();
  });

  it("rejects an objective that is too short before calling the API", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    renderWithProviders(<Tasks />);

    fireEvent.change(screen.getByLabelText(/objective/i), { target: { value: "ab" } });
    fireEvent.click(screen.getByRole("button", { name: /create task/i }));

    expect(await screen.findByText(/at least 3 characters/i)).toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("creates a task and lists it under this session's tasks", async () => {
    const taskBody = {
      id: "task-123",
      objective: "Ship the durable persistence layer",
      priority: "normal",
      status: "pending",
      project_id: null,
      created_at: new Date().toISOString(),
    };
    const fetchMock = vi
      .fn()
      .mockImplementation(
        async () =>
          new Response(JSON.stringify(taskBody), {
            status: 201,
            headers: { "Content-Type": "application/json" },
          })
      );
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<Tasks />);
    fireEvent.change(screen.getByLabelText(/objective/i), {
      target: { value: "Ship the durable persistence layer" },
    });
    fireEvent.click(screen.getByRole("button", { name: /create task/i }));

    await waitFor(() => expect(fetchMock).toHaveBeenCalled());
    const matches = await screen.findAllByText("task-123");
    expect(matches.length).toBeGreaterThan(0);
  });
});
