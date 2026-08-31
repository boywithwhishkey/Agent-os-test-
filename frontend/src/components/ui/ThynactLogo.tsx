import { useId } from "react";

/**
 * The THYNACT monogram, traced from measurements of the brand lockup rather
 * than drawn by eye.
 *
 * Geometry (64-unit box, 1 unit = 1px of the reference at its native size):
 * a round-capped crossbar, a stem that stops SHORT of the curve below it, and
 * a single sinuous stroke that sweeps up from the bottom-left, peaks directly
 * under the stem, and finishes in a short hook to the right.
 *
 * Three details are what make it read as this mark rather than a generic one,
 * and all three were wrong when it was drawn from memory:
 *
 * 1. The stem does not touch the curve. The ~4.5-unit gap is deliberate;
 *    closing it turns the glyph into a solid arch and loses the "T over a
 *    flourish" reading entirely.
 * 2. The right hook is SHORT and ends high — at y≈38, well above the
 *    left tail's y≈60. Extending it to the baseline makes a symmetric arch,
 *    which is the single biggest way this mark gets redrawn wrong.
 * 3. The glyph is taller than it is wide (≈47×52), not squat.
 *
 * Colour: the T is solid `currentColor`, and only the flourish carries the
 * gradient — ink at the tail, warming through the brand magenta, resolving to
 * gold at the hook. Running the gradient across the WHOLE glyph was tried and
 * rejected: the magenta swallowed the crossbar and the mark stopped reading as
 * gold-and-pink, becoming simply purple. Anchoring the T in ink also keeps the
 * mark legible on either theme, since only the ink follows the text colour.
 */
export function ThynactMark({
  className,
  title,
}: {
  className?: string;
  title?: string;
}) {
  // The gradient contains `currentColor`, so it is NOT identical between
  // instances — it resolves against whichever element it is defined under. A
  // shared id would silently point every instance at the first gradient in the
  // document, so two marks in different ink colours on one page would render
  // with the same ink. useId() emits colons, which are legal in url(#...) but
  // not in a CSS selector, so they are stripped.
  const gradientId = `thynact-mark-${useId().replace(/:/g, "")}`;

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
        <linearGradient
          id={gradientId}
          gradientUnits="userSpaceOnUse"
          x1="8.4"
          y1="60.3"
          x2="40.3"
          y2="37.9"
        >
          <stop offset="0%" stopColor="currentColor" />
          <stop offset="34%" stopColor="var(--color-ambient-magenta)" />
          <stop offset="74%" stopColor="var(--color-accent-gold-deep)" />
          <stop offset="100%" stopColor="var(--color-accent-gold-soft)" />
        </linearGradient>
      </defs>

      <g strokeWidth="3" strokeLinecap="round" strokeLinejoin="round">
        {/* Crossbar */}
        <path d="M9.7 8 H55.7" stroke="currentColor" />
        {/* Stem — stops short of the curve, leaving the gap. */}
        <path d="M32.2 8 V27" stroke="currentColor" />
        {/* The flourish: long tail out of the bottom-left, peak under the
            stem, then the short hook right. */}
        <path
          d="M8.4 60.3 C15 54 17 48 22 41 C26 35.4 28.5 31.5 32.5 31.5 C36.5 31.5 38.8 34 40.3 37.9"
          stroke={`url(#${gradientId})`}
        />
      </g>
    </svg>
  );
}

/**
 * Wordmark set in the app's own type at wide tracking, matching the lockup.
 * Kept as text rather than outlined paths so it stays selectable, searchable
 * and legible at small sizes.
 */
export function ThynactWordmark({ className }: { className?: string }) {
  return <span className={className}>THYNACT</span>;
}
