import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type Tone = "neutral" | "violet" | "blue" | "green" | "red" | "amber" | "gold";

const toneStyles: Record<Tone, string> = {
  neutral: "bg-surface-hover text-content-secondary border-surface",
  violet: "bg-accent-gold/10 text-accent-gold border-accent-gold/25",
  blue: "bg-accent-gold-soft/10 text-accent-gold-soft border-accent-gold-soft/25",
  green: "bg-accent-green/10 text-accent-green border-accent-green/25",
  red: "bg-accent-red/10 text-accent-red border-accent-red/25",
  amber: "bg-accent-amber/10 text-accent-amber border-accent-amber/25",
  gold: "bg-accent-gold/10 text-accent-gold border-accent-gold/25",
};

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone;
}

export function Badge({ tone = "neutral", className, children, ...props }: BadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium",
        toneStyles[tone],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
}
