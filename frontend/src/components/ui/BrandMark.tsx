import { cn } from "@/lib/utils";
import { ThynactMark } from "./ThynactLogo";

const TAGLINE = "Built to Think. Powered to Act.";

function Mark({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const dims = size === "sm" ? "h-7 w-7" : size === "lg" ? "h-11 w-11" : "h-9 w-9";
  // The real monogram, with no tile or fill behind it: the mark sits directly
  // on the ambient background the way it does on the brand sheet, and its dark
  // ink follows `currentColor` so one asset serves both themes.
  return (
    <span className={cn("flex shrink-0 items-center justify-center text-content-primary", dims)}>
      <ThynactMark className="h-full w-full" />
    </span>
  );
}

function Wordmark({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const textSize = size === "sm" ? "text-base" : size === "lg" ? "text-2xl" : "text-xl";
  return (
    <span
      className={cn(
        // Weight and tracking are pinned to literal values, NOT the font-medium
        // / tracking-* tokens. Those tokens were retuned lighter for the rest
        // of the site; the logo is excluded from that pass by definition, so it
        // must not follow them when they move again.
        "font-[450] tracking-[0.2em] text-content-primary",
        textSize
      )}
    >
      THYNACT
    </span>
  );
}

/**
 * The THYNACT brand treatment, in three variants:
 * - "mark": icon only, for a collapsed sidebar
 * - "compact": icon + wordmark on one line
 * - "full": the brand-sheet lockup — icon and wordmark on the first line, and
 *   the tagline on a second line that starts just past the MARK'S MIDPOINT.
 *
 *   That indent is measured, not chosen: on the reference lockup the mark spans
 *   x 35-83 (midpoint 59), the tagline's first glyph starts at x 63, and the
 *   wordmark starts at x 97. So the tagline aligns with neither the mark's left
 *   edge nor the wordmark — it begins under the middle of the mark, at ~58% of
 *   the mark's width. Both of the obvious alternatives are wrong.
 */
export function BrandMark({
  variant = "compact",
  size = "md",
  className,
}: {
  variant?: "mark" | "compact" | "full";
  size?: "sm" | "md" | "lg";
  className?: string;
}) {
  if (variant === "mark") return <Mark size={size} />;

  if (variant === "compact") {
    return (
      <div className={cn("flex min-w-0 items-center gap-2.5", className)}>
        <Mark size={size} />
        <Wordmark size={size} />
      </div>
    );
  }

  // ~58% of each size's mark width, so the tagline starts just past the mark's
  // midpoint at every size: 28px -> 16, 36px -> 20, 44px -> 24.
  const taglineIndent = size === "sm" ? "pl-4" : size === "lg" ? "pl-6" : "pl-5";

  return (
    <div className={cn("flex min-w-0 flex-col", className)}>
      <div className="flex items-center gap-2.5">
        <Mark size={size} />
        <Wordmark size={size} />
      </div>
      <span
        className={cn(
          // Weight is pinned, like the wordmark's: the tagline belongs to the
          // logo lockup and stays out of the site-wide type tokens.
          "truncate font-[350] tracking-[0.01em] text-content-muted",
          taglineIndent,
          size === "lg" ? "mt-1 text-sm" : "mt-0.5 text-[11px]"
        )}
      >
        {TAGLINE}
      </span>
    </div>
  );
}

export { TAGLINE as BRAND_TAGLINE };
