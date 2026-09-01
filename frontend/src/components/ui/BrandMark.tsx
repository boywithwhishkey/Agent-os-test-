import { cn } from "@/lib/utils";
import { ThynactMark, ThynactWordmark } from "./ThynactLogo";

const TAGLINE = "Built to Think. Powered to Act.";

type Size = "sm" | "md" | "lg";

/**
 * Brand lockups.
 *
 * Sizing is expressed as a mark height plus a wordmark WIDTH, because the two
 * assets have very different aspect ratios and matching them by height alone
 * puts the wordmark's optical weight wildly out of step with the mark.
 *
 * `tracking` tightens only the wordmark's inter-letter gap. The brand sheet's
 * own spacing is right at banner width but far too wide for a 256px sidebar,
 * so compact placements tighten it rather than shrinking the wordmark until it
 * is unreadable — the full horizontal lockup is never forced into the sidebar.
 */
const SIZES: Record<
  Size,
  { mark: string; word: string; gap: string; tracking: number; tagline: string }
> = {
  sm: { mark: "h-7 w-7", word: "w-[104px]", gap: "gap-3", tracking: 0.4, tagline: "text-[10px]" },
  md: { mark: "h-9 w-9", word: "w-[140px]", gap: "gap-4", tracking: 0.42, tagline: "text-[11px]" },
  lg: { mark: "h-12 w-12", word: "w-[250px]", gap: "gap-8", tracking: 0.6, tagline: "text-sm" },
};

function Mark({ size }: { size: Size }) {
  return (
    <span className={cn("flex shrink-0 items-center justify-center text-content-primary", SIZES[size].mark)}>
      <ThynactMark className="h-full w-full" />
    </span>
  );
}

function Wordmark({ size }: { size: Size }) {
  return (
    <ThynactWordmark
      // max-w-full + shrink, NOT shrink-0: at 320px the hero lockup is wider
      // than the viewport, and a fixed-width wordmark was being clipped to
      // "THYNAC" by an overflow-hidden ancestor. Because it was clipped rather
      // than overflowing, no horizontal-overflow check could catch it — only
      // looking at the render did. An SVG with a width and a viewBox scales its
      // height automatically, so shrinking stays proportional.
      className={cn("min-w-0 max-w-full text-content-primary", SIZES[size].word)}
      tracking={SIZES[size].tracking}
    />
  );
}

/**
 * - "mark": icon only, for a collapsed sidebar or a tight control
 * - "compact": mark + wordmark on one line
 * - "full": adds the product tagline on a second line, starting just past the
 *   mark's midpoint (measured off the sheet: mark x 35-83, tagline ink from
 *   x 63 — it aligns with neither the mark's left edge nor the wordmark).
 */
export function BrandMark({
  variant = "compact",
  size = "md",
  className,
}: {
  variant?: "mark" | "compact" | "full";
  size?: Size;
  className?: string;
}) {
  if (variant === "mark") return <Mark size={size} />;

  // The sheet sets the mark and wordmark 162px apart against a 226px mark
  // (~0.7x the mark's width). A flat gap-2.5 let the crossbar collide with the
  // "T" at hero size, so the gap scales with the mark.
  const lockup = (
    <div className={cn("flex min-w-0 items-center", SIZES[size].gap)}>
      <Mark size={size} />
      <Wordmark size={size} />
    </div>
  );

  if (variant === "compact") return <div className={cn("min-w-0", className)}>{lockup}</div>;

  // ~58% of the mark's width at each size, so the tagline starts just past the
  // mark's midpoint: 28px -> 16, 36px -> 20, 48px -> 28.
  const indent = size === "sm" ? "pl-4" : size === "lg" ? "pl-7" : "pl-5";

  return (
    <div className={cn("flex min-w-0 flex-col", className)}>
      {lockup}
      <span
        className={cn(
          // Weight pinned, not tokenised: the tagline belongs to the lockup and
          // stays out of the site-wide type scale.
          "truncate font-[350] tracking-[0.01em] text-content-muted",
          indent,
          SIZES[size].tagline,
          size === "lg" ? "mt-1.5" : "mt-1"
        )}
      >
        {TAGLINE}
      </span>
    </div>
  );
}

export { TAGLINE as BRAND_TAGLINE };
