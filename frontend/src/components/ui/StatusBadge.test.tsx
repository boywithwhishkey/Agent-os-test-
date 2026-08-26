import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { StatusBadge } from "./StatusBadge";

describe("StatusBadge", () => {
  it("renders a human label, not the raw status token", () => {
    render(<StatusBadge status="waiting_approval" />);
    expect(screen.getByText("Waiting approval")).toBeInTheDocument();
  });

  it("falls back to the raw value for unknown statuses", () => {
    render(<StatusBadge status="mystery" />);
    expect(screen.getByText("mystery")).toBeInTheDocument();
  });
});
