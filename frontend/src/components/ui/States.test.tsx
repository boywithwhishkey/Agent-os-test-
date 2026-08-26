import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ErrorState, EmptyState, LoadingState } from "./States";
import { ApiError } from "@/lib/api/client";

describe("global UX states", () => {
  it("shows an authentication message for 401 ApiErrors", () => {
    const error = new ApiError({ status: 401, detail: "Unauthorized", correlationId: "corr-1" });
    render(<ErrorState error={error} />);
    expect(screen.getByText("Authentication required")).toBeInTheDocument();
    expect(screen.getByText(/corr-1/)).toBeInTheDocument();
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
