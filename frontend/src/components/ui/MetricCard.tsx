import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export function MetricCard({
  label,
  value,
  icon,
  tone = "neutral",
  hint,
}: {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
  tone?: "neutral" | "violet" | "blue" | "green" | "red" | "amber";
  hint?: string;
}) {
  const toneStyles: Record<string, string> = {
    neutral: "text-content-primary",
    violet: "text-accent-violet",
    blue: "text-accent-blue",
    green: "text-accent-green",
    red: "text-accent-red",
    amber: "text-accent-amber",
  };
  return (
    <div className="rounded-xl border border-surface bg-surface-raised p-4">
      <div className="flex items-center justify-between">
        <p className="text-xs font-medium text-content-muted">{label}</p>
        {icon && <span className={cn("text-content-muted", toneStyles[tone])}>{icon}</span>}
      </div>
      <p className={cn("mt-2 text-2xl font-semibold tabular-nums", toneStyles[tone])}>{value}</p>
      {hint && <p className="mt-1 text-xs text-content-muted">{hint}</p>}
    </div>
  );
}
