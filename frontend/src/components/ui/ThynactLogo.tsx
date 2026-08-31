/**
 * The THYNACT monogram: a "T" whose stem is crossed by a rising curve that
 * falls away to the right, forming the apex of an "A". The descending right
 * leg carries the gold gradient — the one place the brand colour appears in
 * the mark itself.
 *
 * Drawn as strokes rather than filled paths so it stays crisp at 20px in the
 * sidebar and at 44px in the dashboard hero without needing two assets, and so
 * it can inherit `currentColor` for the dark strokes. That inheritance is why
 * the mark works on both themes from one file: the ink follows the text
 * colour, only the gold is fixed.
 */
export function ThynactMark({
  className,
  title,
}: {
  className?: string;
  title?: string;
}) {
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
        {/* Unique id is not needed: the gradient is identical everywhere the
            mark renders, so a shared id is correct and avoids duplicate defs. */}
        <linearGradient id="thynact-gold" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stopColor="var(--color-accent-gold-deep)" />
          <stop offset="55%" stopColor="var(--color-accent-gold)" />
          <stop offset="100%" stopColor="var(--color-accent-gold-soft)" />
        </linearGradient>
      </defs>

      <g
        stroke="currentColor"
        strokeWidth="3"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        {/* Crossbar and stem of the T */}
        <path d="M13 15 H51" />
        <path d="M32 15 V36" />
        {/* Rising left flank of the curve */}
        <path d="M9 53 C19 53 22 29 33 29" />
      </g>

      {/* Falling right leg — the gold accent, drawn last so it sits above the
          dark ink where the two meet at the apex. */}
      <path
        d="M33 29 C43 29 45 44 51 53"
        stroke="url(#thynact-gold)"
        strokeWidth="3"
        strokeLinecap="round"
        fill="none"
      />
    </svg>
  );
}

/**
 * Wordmark set in the app's own type at wide tracking, matching the logo
 * lockup. Kept as text rather than an SVG outline so it stays selectable,
 * searchable and legible at small sizes.
 */
export function ThynactWordmark({ className }: { className?: string }) {
  return <span className={className}>THYNACT</span>;
}
