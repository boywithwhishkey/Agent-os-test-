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
 * - "full": the brand-sheet lockup — icon and wordmark on the first line, with
 *   the tagline on a second line running the full width beneath BOTH, rather
 *   than indented into a column beside the mark.
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

  return (
    <div className={cn("flex min-w-0 flex-col", className)}>
      <div className="flex items-center gap-2.5">
        <Mark size={size} />
        <Wordmark size={size} />
      </div>
      <span
        className={cn(
          // Also pinned: the tagline belongs to the logo lockup.
          "truncate font-[350] tracking-[0.01em] text-content-muted",
          size === "lg" ? "mt-1 text-sm" : "mt-0.5 text-[11px]"
        )}
      >
        {TAGLINE}
      </span>
    </div>
  );
}

export { TAGLINE as BRAND_TAGLINE };
