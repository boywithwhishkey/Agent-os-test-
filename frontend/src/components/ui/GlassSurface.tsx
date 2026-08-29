import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type GlassLevel = "ambient" | "soft" | "panel" | "focus";

const levelClass: Record<GlassLevel, string> = {
  ambient: "glass-ambient",
  soft: "glass-soft",
  panel: "glass-panel",
  focus: "glass-focus",
};

interface GlassSurfaceProps extends HTMLAttributes<HTMLDivElement> {
  level?: GlassLevel;
  /** Adds a hairline tonal edge instead of a bright border. Off by default — depth comes from opacity, not outlines. */
  hairline?: boolean;
}

/**
 * The base translucent-pane primitive for THYNACT's "infinite canvas" design
 * language — depth via blur/opacity instead of hard-bordered cards.
 */
export function GlassSurface({ level = "panel", hairline = false, className, ...props }: GlassSurfaceProps) {
  return (
    <div
      className={cn(
        "rounded-2xl",
        levelClass[level],
        hairline && "border border-hairline",
        className
      )}
      {...props}
    />
  );
}
