import { useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

export type HeartbeatState = "online" | "connecting" | "offline";

// One stylized ECG cycle in an 0..40 x 0..24 unit box, baseline y=12:
// flat → small P-wave bump → sharp QRS spike → small T-wave bump → flat.
const ECG_CYCLE = "M0,12 L8,12 L11,9 L14,12 L18,12 L21,2 L24,22 L27,12 L31,12 L34,8 L37,12 L40,12";

const stroke: Record<HeartbeatState, string> = {
  online: "stroke-accent-green",
  connecting: "stroke-accent-amber",
  offline: "stroke-accent-red",
};

/**
 * Replaces a plain "online/offline" dot with an ECG-style trace — used in
 * the top-right API status pill and the Dashboard API status metric.
 * Online: a continuously scrolling two-cycle waveform (SMIL <animateTransform>,
 * not CSS — SMIL translate values stay in the SVG's own coordinate system
 * regardless of how the element is scaled on screen, so the loop is exact).
 * Connecting: the same waveform, static, breathing opacity.
 * Offline: a flat straight line — calm, not gimmicky, no motion implied.
 */
export function HeartbeatLine({
  state,
  className,
  width = 56,
  height = 20,
}: {
  state: HeartbeatState;
  className?: string;
  width?: number;
  height?: number;
}) {
  const reduceMotion = useReducedMotion();

  if (state === "offline") {
    return (
      <svg viewBox="0 0 40 24" width={width} height={height} className={cn(stroke.offline, className)} aria-hidden>
        <line x1="0" y1="12" x2="40" y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
    );
  }

  if (state === "connecting" || reduceMotion) {
    return (
      <svg
        viewBox="0 0 40 24"
        width={width}
        height={height}
        className={cn(stroke[state], state === "connecting" && !reduceMotion && "animate-ecg-breathe", className)}
        aria-hidden
      >
        <path d={ECG_CYCLE} fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }

  return (
    // The root <svg> clips to its viewBox by default (UA overflow:hidden) —
    // that's what turns two back-to-back cycles sliding left into a
    // seamless, indefinitely-scrolling one-cycle-wide window.
    <svg viewBox="0 0 40 24" width={width} height={height} className={cn(stroke.online, className)} aria-hidden>
      <g fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d={ECG_CYCLE} />
        <path d={ECG_CYCLE} transform="translate(40, 0)" />
        <animateTransform attributeName="transform" type="translate" from="0 0" to="-40 0" dur="1.8s" repeatCount="indefinite" />
      </g>
    </svg>
  );
}
