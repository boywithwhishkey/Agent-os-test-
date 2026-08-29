import { Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";

const TAGLINE = "Built to Think. Powered to Act.";

function Mark({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const dims = size === "sm" ? "h-7 w-7" : size === "lg" ? "h-11 w-11" : "h-9 w-9";
  const iconDims = size === "sm" ? "h-4 w-4" : size === "lg" ? "h-6 w-6" : "h-5 w-5";
  return (
    <span
      className={cn(
        "flex shrink-0 items-center justify-center rounded-xl bg-gradient-to-br from-accent-violet to-accent-blue text-white shadow-[0_0_20px_-4px_var(--color-accent-violet)]",
        dims
      )}
    >
      <Sparkles className={iconDims} />
    </span>
  );
}

function Wordmark({ size = "md" }: { size?: "sm" | "md" | "lg" }) {
  const textSize = size === "sm" ? "text-sm" : size === "lg" ? "text-2xl" : "text-lg";
  return (
    <span
      className={cn(
        "bg-gradient-to-r from-accent-violet-soft via-accent-blue to-accent-violet-soft bg-clip-text font-semibold tracking-tight text-transparent",
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
