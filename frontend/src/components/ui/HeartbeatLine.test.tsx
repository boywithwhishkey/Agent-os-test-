import { describe, it, expect, vi, afterEach } from "vitest";
import { render } from "@testing-library/react";
import { HeartbeatLine } from "./HeartbeatLine";

vi.mock("framer-motion", async (importOriginal) => {
  const actual = await importOriginal<typeof import("framer-motion")>();
  return { ...actual, useReducedMotion: vi.fn(() => false) };
});

import { useReducedMotion } from "framer-motion";
const mockUseReducedMotion = vi.mocked(useReducedMotion);

describe("HeartbeatLine", () => {
  afterEach(() => {
    mockUseReducedMotion.mockReturnValue(false);
  });

  it("online renders an animated multi-cycle waveform (animateTransform present)", () => {
    const { container } = render(<HeartbeatLine state="online" width={80} height={20} />);
    const svg = container.querySelector("svg")!;
    expect(svg).toHaveClass("stroke-accent-green");
    expect(container.querySelectorAll("path").length).toBeGreaterThanOrEqual(2);
    expect(container.querySelector("animateTransform")).toBeInTheDocument();
  });

  it("a wider online instance renders more repeated cycles, not a stretched single one", () => {
    const narrow = render(<HeartbeatLine state="online" width={40} height={24} />);
    const wide = render(<HeartbeatLine state="online" width={160} height={24} />);
    const narrowCycles = narrow.container.querySelectorAll("path").length;
    const wideCycles = wide.container.querySelectorAll("path").length;
    expect(wideCycles).toBeGreaterThan(narrowCycles);
  });

  it("offline renders a static straight line with no waveform path or animation", () => {
    const { container } = render(<HeartbeatLine state="offline" />);
    const svg = container.querySelector("svg")!;
    expect(svg).toHaveClass("stroke-accent-red");
    expect(container.querySelector("line")).toBeInTheDocument();
    expect(container.querySelector("path")).not.toBeInTheDocument();
    expect(container.querySelector("animateTransform")).not.toBeInTheDocument();
  });

  it("connecting renders a static amber waveform (breathing opacity, no scroll animation)", () => {
    const { container } = render(<HeartbeatLine state="connecting" />);
    const svg = container.querySelector("svg")!;
    expect(svg).toHaveClass("stroke-accent-amber");
    expect(svg).toHaveClass("animate-ecg-breathe");
    expect(container.querySelector("path")).toBeInTheDocument();
    expect(container.querySelector("animateTransform")).not.toBeInTheDocument();
  });

  it("respects prefers-reduced-motion: online falls back to a static waveform, state stays visible", () => {
    mockUseReducedMotion.mockReturnValue(true);
    const { container } = render(<HeartbeatLine state="online" />);
    const svg = container.querySelector("svg")!;
    // Still communicates "online" via color + a visible waveform shape...
    expect(svg).toHaveClass("stroke-accent-green");
    expect(container.querySelector("path")).toBeInTheDocument();
    // ...but the continuous scroll animation is gone, and it doesn't breathe either
    // (breathing is reserved for "connecting" — reduced motion shouldn't invent motion).
    expect(container.querySelector("animateTransform")).not.toBeInTheDocument();
    expect(svg).not.toHaveClass("animate-ecg-breathe");
  });
});
