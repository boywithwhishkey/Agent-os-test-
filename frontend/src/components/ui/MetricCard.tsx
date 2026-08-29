import type { ReactNode } from "react";
import { motion } from "framer-motion";
import { metricReveal } from "@/lib/motion";
import { cn } from "@/lib/utils";

export function MetricCard({
  label,
  value,
  icon,
  tone = "neutral",
  hint,
  graphic,
}: {
  label: string;
  value: ReactNode;
  icon?: ReactNode;
  tone?: "neutral" | "violet" | "blue" | "green" | "red" | "amber";
  hint?: string;
  /** Optional small visual under the hint — e.g. a HeartbeatLine for the API status metric. */
  graphic?: ReactNode;
}) {
  const toneStyles: Record<string, string> = {
    neutral: "text-content-primary",
    violet: "text-accent-violet",
    blue: "text-accent-blue",
    green: "text-accent-green",
    red: "text-accent-red",
    amber: "text-accent-amber",
  };
  const glowStyles: Record<string, string> = {
    neutral: "bg-content-primary/[0.03]",
    violet: "bg-accent-violet/[0.06]",
    blue: "bg-accent-blue/[0.06]",
    green: "bg-accent-green/[0.06]",
    red: "bg-accent-red/[0.06]",
    amber: "bg-accent-amber/[0.06]",
  };
  return (
    <motion.div
      variants={metricReveal}
      className="glass-soft relative flex h-full flex-col overflow-hidden rounded-2xl border border-hairline p-5"
    >
      <div className={cn("pointer-events-none absolute -right-6 -top-6 h-24 w-24 rounded-full blur-2xl", glowStyles[tone])} aria-hidden />
      <div className="relative flex items-center justify-between">
        <p className="text-xs font-medium uppercase tracking-wide text-content-muted">{label}</p>
        {icon && <span className={cn("text-content-muted", toneStyles[tone])}>{icon}</span>}
      </div>
      <motion.p
        key={String(value)}
        initial={{ opacity: 0, y: 4 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
        className={cn("relative mt-2.5 text-[1.75rem] font-semibold tracking-tight tabular-nums", toneStyles[tone])}
      >
        {value}
      </motion.p>
      {hint && <p className="relative mt-1.5 text-xs text-content-muted">{hint}</p>}
      {graphic && <div className="relative mt-2.5">{graphic}</div>}
    </motion.div>
  );
}
