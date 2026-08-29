import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { ErrorState, EmptyState, LoadingState } from "./States";
import { ApiError } from "@/lib/api/client";

describe("global UX states", () => {
  it("shows a neutral setup banner (not a red error panel) for 401 ApiErrors", () => {
    const error = new ApiError({ status: 401, detail: "Unauthorized", correlationId: "corr-1" });
    render(<ErrorState error={error} />, { wrapper: MemoryRouter });
    expect(screen.getByText("Unauthorized")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /configure api key/i })).toBeInTheDocument();
    // Must not use the alarm-red genuine-error treatment for a setup state.
    expect(screen.queryByText("Authentication required")).not.toBeInTheDocument();
  });

  it("shows the same neutral banner for a 503 (backend has no operator key configured)", () => {
    const error = new ApiError({ status: 503, detail: "API authentication is not configured", correlationId: null });
    render(<ErrorState error={error} />, { wrapper: MemoryRouter });
    expect(screen.getByText("API authentication is not configured")).toBeInTheDocument();
  });

  it("shows a network message for network ApiErrors", () => {
    const error = new ApiError({ status: 0, detail: "offline", correlationId: null, isNetworkError: true });
    render(<ErrorState error={error} />);
    expect(screen.getByText("Can't reach the API")).toBeInTheDocument();
  });

  it("renders empty state title and description", () => {
    render(<EmptyState title="Nothing here" description="Create one to get started." />);
    expect(screen.getByText("Nothing here")).toBeInTheDocument();
    expect(screen.getByText("Create one to get started.")).toBeInTheDocument();
  });

  it("renders a loading state with status role", () => {
    render(<LoadingState label="Fetching…" />);
    expect(screen.getByRole("status")).toHaveTextContent("Fetching…");
  });
});
