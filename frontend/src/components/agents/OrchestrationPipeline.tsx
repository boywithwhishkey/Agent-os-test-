import { motion } from "framer-motion";
import { Search, Hammer, Eye, Check, X } from "lucide-react";
import { cn } from "@/lib/utils";
import type { AgentCardStatus } from "./AgentCard";

const STEPS: { role: string; label: string; icon: typeof Search }[] = [
  { role: "researcher", label: "Researcher", icon: Search },
  { role: "builder", label: "Builder", icon: Hammer },
  { role: "reviewer", label: "Reviewer", icon: Eye },
];

const ringClass: Record<AgentCardStatus, string> = {
  pending: "border-hairline text-content-muted",
  running: "border-accent-blue text-accent-blue shadow-[0_0_18px_-3px_var(--color-accent-blue)] animate-pulse-slow",
  success: "border-accent-green text-accent-green bg-accent-green/10",
  failed: "border-accent-red text-accent-red bg-accent-red/10",
};

/** Visualizes the fixed researcher → builder → reviewer orchestration flow. */
export function OrchestrationPipeline({ statuses }: { statuses: Record<string, AgentCardStatus> }) {
  return (
    <div className="flex items-center gap-2 overflow-x-auto py-2" aria-label="Orchestration pipeline">
      {STEPS.map((step, i) => {
        const status = statuses[step.role] ?? "pending";
        const prevDone = i === 0 || (statuses[STEPS[i - 1].role] ?? "pending") === "success";
        return (
          <div key={step.role} className="flex shrink-0 items-center gap-2">
            {i > 0 && (
              <div className="relative h-0.5 w-8 shrink-0 overflow-hidden rounded-full bg-surface sm:w-14">
                <motion.div
                  className="absolute inset-y-0 left-0 bg-accent-violet"
                  initial={{ width: "0%" }}
                  animate={{ width: prevDone ? "100%" : "0%" }}
                  transition={{ duration: 0.5, ease: "easeOut" }}
                />
              </div>
            )}
            <motion.div
              initial={{ opacity: 0, y: 6 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.08, duration: 0.3 }}
              className="flex flex-col items-center gap-1.5"
            >
              <span
                className={cn(
                  "flex h-11 w-11 items-center justify-center rounded-full border-2 bg-surface-raised transition-colors",
                  ringClass[status]
                )}
              >
                {status === "success" ? (
                  <Check className="h-4.5 w-4.5" />
                ) : status === "failed" ? (
                  <X className="h-4.5 w-4.5" />
                ) : (
                  <step.icon className="h-4.5 w-4.5" />
                )}
              </span>
              <span className="text-[11px] font-medium text-content-secondary">{step.label}</span>
            </motion.div>
          </div>
        );
      })}
    </div>
  );
}
