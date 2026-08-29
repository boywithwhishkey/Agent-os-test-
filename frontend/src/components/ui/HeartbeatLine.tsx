import { useReducedMotion } from "framer-motion";
import { cn } from "@/lib/utils";

export type HeartbeatState = "online" | "connecting" | "offline";

// One stylized ECG cycle in a 40-wide x 24-tall unit box, baseline y=12:
// flat → small P-wave bump → sharp QRS spike → small T-wave bump → flat.
const CYCLE_W = 40;
const CYCLE_H = 24;
const ECG_CYCLE = "M0,12 L8,12 L11,9 L14,12 L18,12 L21,2 L24,22 L27,12 L31,12 L34,8 L37,12 L40,12";

const stroke: Record<HeartbeatState, string> = {
  online: "stroke-accent-green",
  connecting: "stroke-accent-amber",
  offline: "stroke-accent-red",
};

/**
 * Replaces a plain "online/offline" dot with an ECG-style trace — used in
 * the top-right API status pill and the Dashboard API status metric.
 *
 * Online: a continuously scrolling multi-cycle waveform (SMIL
 * <animateTransform>, not CSS — SMIL translate values stay in the SVG's
 * own coordinate system regardless of how the element is scaled on
 * screen, so the loop is exact). The viewBox width is derived from the
 * requested pixel aspect ratio (not hardcoded to one cycle) so a wider
 * instance genuinely renders more traveling peaks instead of letterboxing
 * a single stretched cycle in empty space.
 * Connecting: the same multi-cycle waveform, static, breathing opacity.
 * Offline: a flat straight line spanning the full width — calm, not
 * gimmicky, no motion implied.
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

  // Scale the viewBox to match the requested aspect ratio exactly, so the
  // default "meet" preserveAspectRatio never letterboxes — the box always
  // shows genuinely more waveform, not a stretched/padded single cycle.
  const unitsWide = Math.max(CYCLE_W, CYCLE_H * (width / height));
  const viewBox = `0 0 ${unitsWide} ${CYCLE_H}`;
  const cycles = Math.max(1, Math.ceil(unitsWide / CYCLE_W));

  if (state === "offline") {
    return (
      <svg viewBox={viewBox} width={width} height={height} className={cn(stroke.offline, className)} aria-hidden>
        <line x1="0" y1="12" x2={unitsWide} y2="12" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      </svg>
    );
  }

  if (state === "connecting" || reduceMotion) {
    return (
      <svg
        viewBox={viewBox}
        width={width}
        height={height}
        className={cn(stroke[state], state === "connecting" && !reduceMotion && "animate-ecg-breathe", className)}
        aria-hidden
      >
        <g fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          {Array.from({ length: cycles }).map((_, i) => (
            <path key={i} d={ECG_CYCLE} transform={`translate(${i * CYCLE_W}, 0)`} />
          ))}
        </g>
      </svg>
    );
  }

  return (
    // The root <svg> clips to its viewBox by default (UA overflow:hidden) —
    // that's what turns (cycles + 1) back-to-back cycles sliding left by
    // exactly one cycle-width into a seamless, indefinitely-scrolling
    // strip: whatever exits on the left is identical to what's about to
    // enter on the right, so the repeatCount="indefinite" reset is
    // imperceptible — no visible restart, blink, or seam.
    <svg viewBox={viewBox} width={width} height={height} className={cn(stroke.online, className)} aria-hidden>
      <g fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        {Array.from({ length: cycles + 1 }).map((_, i) => (
          <path key={i} d={ECG_CYCLE} transform={`translate(${i * CYCLE_W}, 0)`} />
        ))}
        <animateTransform
          attributeName="transform"
          type="translate"
          from="0 0"
          to={`-${CYCLE_W} 0`}
          dur="1.8s"
          repeatCount="indefinite"
        />
      </g>
    </svg>
  );
}
