import { cn } from "@/lib/utils";
import { ThynactMark } from "./ThynactLogo";

const TAGLINE = "Built to Think. Powered to Act.";

function Mark({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const dims = size === "sm" ? "h-7 w-7" : size === "lg" ? "h-11 w-11" : "h-9 w-9";
  // The real monogram replaces the old generic "sparkles in a gradient tile".
  // No tile, no fill: the mark sits directly on the ambient background the way
  // it does on the brand sheet, and its dark ink follows `currentColor` so one
  // asset serves both themes.
  return (
    <span className={cn("flex shrink-0 items-center justify-center text-content-primary", dims)}>
      <ThynactMark className="h-full w-full" />
    </span>
  );
}

function Wordmark({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const textSize = size === "sm" ? "text-sm" : size === "lg" ? "text-2xl" : "text-lg";
  return (
    <span
      className={cn(
        // Wide tracking and a light weight to match the logo lockup, in the
        // app's own ink rather than a coloured gradient — the gold belongs to
        // the mark, and repeating it in the word made the pair compete.
        "font-medium tracking-[0.18em] text-content-primary",
        textSize
      )}
    >
      THYNACT
    </span>
  );
}

/**
 * The THYNACT brand treatment, in three sizes:
 * - "mark": icon only, for a collapsed sidebar
 * - "compact": icon + wordmark, for the sidebar header / splash contexts
 * - "full": icon + wordmark + tagline, for the dashboard hero and about/settings
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

  return (
    <div className={cn("flex items-center gap-2.5", className)}>
      <Mark size={size} />
      <div className="flex min-w-0 flex-col leading-tight">
        <Wordmark size={size} />
        {variant === "full" && (
          <span className="truncate text-xs text-content-muted">{TAGLINE}</span>
        )}
      </div>
    </div>
  );
}

export { TAGLINE as BRAND_TAGLINE };
