import { useId } from "react";

/**
 * THYNACT brand marks, traced from measurements of the approved brand sheet
 * rather than drawn by eye. Both are STROKED geometry, not filled outlines:
 * the whole identity uses one uniform stroke weight (12px at the sheet's
 * cap-height of 97), so strokes reproduce it exactly, stay crisp at every size,
 * and keep the assets to a few hundred bytes.
 *
 * Measured from the sheet (mark region x 284-509, y 240-470):
 *  - crossbar  y=244, x 310-509, ~8px stroke (lighter than the rest)
 *  - stem      x=409, y 248-335, ~12px stroke
 *  - arch      peak ~(423,347), left tail to (288,469), right leg to (507,468)
 *  - gold      x 490-509, y 424-468 — the lower third of the RIGHT LEG only
 *
 * The arch is a full arch whose right leg runs all the way to the baseline,
 * mirroring the left tail. An earlier version drew it as a short hook stopping
 * high, because it was traced from a low-resolution screenshot of the app's own
 * (already incorrect) rendering instead of from the brand sheet. Trace the
 * sheet, never the app.
 */

/** Ink→gold stop positions, shared by the mark and the favicon. */
const GOLD_STOPS = (
  <>
    <stop offset="0%" stopColor="currentColor" />
    <stop offset="48%" stopColor="currentColor" />
    <stop offset="68%" stopColor="var(--color-accent-gold-deep)" />
    <stop offset="100%" stopColor="var(--color-accent-gold-soft)" />
  </>
);

export function ThynactMark({ className, title }: { className?: string; title?: string }) {
  // The gradient resolves `currentColor` against its own element, so it is NOT
  // identical between instances. A shared id would point every instance at the
  // first gradient in the document, rendering two marks of different ink
  // colours identically — which is exactly what happened when proofing light
  // and dark swatches on one page. useId() emits colons; they are legal in
  // url(#…) but not in a CSS selector, so they are stripped.
  const gid = `thynact-arch-${useId().replace(/:/g, "")}`;

  return (
    <svg
      viewBox="0 0 64 64"
      fill="none"
      className={className}
      role={title ? "img" : undefined}
      aria-label={title}
      aria-hidden={title ? undefined : true}
    >
      <defs>
        {/* Horizontal axis spanning only the right leg: everything further left
            — the apex and the whole left tail — clamps to the first stop and
            stays ink, so the gold lands on the leg alone, as on the sheet. */}
        <linearGradient id={gid} gradientUnits="userSpaceOnUse" x1="46" y1="0" x2="59" y2="0">
          {GOLD_STOPS}
        </linearGradient>
      </defs>

      <g strokeLinecap="round" strokeLinejoin="round">
        {/* Crossbar — measurably lighter than the stem on the sheet (8px vs
            12px). Kept at 2.3 rather than a true-to-scale 1.9 so it survives
            at favicon and collapsed-sidebar sizes. */}
        <path d="M10.9 5 H59.1" stroke="currentColor" strokeWidth="2.3" />
        {/* Stem — runs down into the arch. On the sheet the stem's cap and the
            arch's crown meet tangentially; overlapping them slightly here
            guarantees no hairline seam at any raster size. */}
        <path d="M35.1 5 V30" stroke="currentColor" strokeWidth="2.9" />
        {/* Arch: left tail, crown, right leg to the baseline. */}
        <path
          d="M5.7 59.5 C11 58.8 16.5 54 19.6 48.8 C22.5 44.5 25.5 38.5 29.7 34.3 C33.5 28.6 42.5 28.6 46.2 34.3 C50.5 39.5 55 48 58.6 59.3"
          stroke={`url(#${gid})`}
          strokeWidth="2.9"
        />
      </g>
    </svg>
  );
}

/**
 * The THYNACT wordmark as stroked geometry.
 *
 * Built rather than typeset because the sheet's "A" has NO crossbar — it
 * carries a gold dot in its counter instead, which no font will produce. The
 * letters are otherwise plain geometric strokes, so drawing them costs little
 * and matches the sheet exactly.
 *
 * Coordinates: cap height 100, baseline y=100, uniform stroke 12, letters
 * separated by a measured 95-unit gap (the sheet's advances vary 83-102; the
 * spread is measurement noise on a rasterised sheet, so one value is used).
 *
 * `tracking` scales only the inter-letter gap. The sheet's own spacing (~0.64em
 * equivalent) is beautiful at banner width but too wide for a 256px sidebar, so
 * compact placements tighten it rather than shrinking the wordmark to
 * illegibility — per the brand rule that the full horizontal lockup is not
 * forced into the sidebar.
 */
export function ThynactWordmark({
  className,
  tracking = 1,
}: {
  className?: string;
  tracking?: number;
}) {
  const gid = `thynact-a-${useId().replace(/:/g, "")}`;
  const gap = 95 * tracking;

  // [ink width, render(x) -> paths]
  const letters: Array<[number, (x: number) => React.ReactNode]> = [
    // T
    [87.6, (x) => <path key={`t1${x}`} d={`M${x + 6} 6 H${x + 81.6} M${x + 43.8} 6 V94`} />],
    // H
    [
      96.9,
      (x) => (
        <path key={`h${x}`} d={`M${x + 6} 6 V94 M${x + 90.9} 6 V94 M${x + 6} 50 H${x + 90.9}`} />
      ),
    ],
    // Y
    [
      92.8,
      (x) => (
        <path
          key={`y${x}`}
          d={`M${x + 6} 6 L${x + 46.4} 50 L${x + 86.8} 6 M${x + 46.4} 50 V94`}
        />
      ),
    ],
    // N
    [
      107.2,
      (x) => (
        <path
          key={`n${x}`}
          d={`M${x + 6} 6 V94 M${x + 101.2} 6 V94 M${x + 6} 6 L${x + 101.2} 94`}
        />
      ),
    ],
    // A — apex and two legs, deliberately no crossbar.
    [
      111.3,
      (x) => (
        <path key={`a${x}`} d={`M${x + 6} 94 L${x + 55.65} 6 L${x + 105.3} 94`} />
      ),
    ],
    // C
    [92.8, (x) => <path key={`c${x}`} d={`M${x + 72.8} 16.3 A41 44 0 1 0 ${x + 72.8} 83.7`} />],
    // T
    [86.6, (x) => <path key={`t2${x}`} d={`M${x + 6} 6 H${x + 80.6} M${x + 43.3} 6 V94`} />],
  ];

  let cursor = 0;
  const placed: React.ReactNode[] = [];
  let aCenter = 0;
  letters.forEach(([w, render], i) => {
    placed.push(render(cursor));
    if (i === 4) aCenter = cursor + 55.65;
    cursor += w + (i < letters.length - 1 ? gap : 0);
  });
  const total = cursor;

  return (
    <svg
      viewBox={`-7 -7 ${total + 14} 114`}
      fill="none"
      className={className}
      role="img"
      aria-label="THYNACT"
    >
      <defs>
        <linearGradient id={gid} x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="var(--color-accent-gold-deep)" />
          <stop offset="100%" stopColor="var(--color-accent-gold-soft)" />
        </linearGradient>
      </defs>
      <g stroke="currentColor" strokeWidth="12" strokeLinecap="round" strokeLinejoin="round">
        {placed}
      </g>
      {/* The gold dot in the A's counter — the sheet's one wordmark accent. */}
      <circle cx={aCenter} cy="72" r="7" fill={`url(#${gid})`} stroke="none" />
    </svg>
  );
}
