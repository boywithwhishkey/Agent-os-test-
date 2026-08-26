import { Badge } from "./Badge";
import { cn } from "@/lib/utils";

export type StatusKind =
  | "pending"
  | "running"
  | "completed"
  | "succeeded"
  | "failed"
  | "rejected"
  | "paused"
  | "skipped"
  | "waiting_approval"
  | "ok"
  | "unconfigured"
  | "unavailable"
  | "healthy"
  | "degraded";

const config: Record<StatusKind, { label: string; tone: "neutral" | "violet" | "blue" | "green" | "red" | "amber"; pulse?: boolean }> = {
  pending: { label: "Pending", tone: "neutral" },
  running: { label: "Running", tone: "blue", pulse: true },
  completed: { label: "Completed", tone: "green" },
  succeeded: { label: "Succeeded", tone: "green" },
  failed: { label: "Failed", tone: "red" },
  rejected: { label: "Rejected", tone: "red" },
  paused: { label: "Paused", tone: "amber" },
  skipped: { label: "Skipped", tone: "neutral" },
  waiting_approval: { label: "Waiting approval", tone: "amber", pulse: true },
  ok: { label: "Healthy", tone: "green" },
  healthy: { label: "Healthy", tone: "green" },
  unconfigured: { label: "Unconfigured", tone: "neutral" },
  unavailable: { label: "Unavailable", tone: "red" },
  degraded: { label: "Degraded", tone: "amber" },
};

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  const entry = config[status as StatusKind] ?? { label: status, tone: "neutral" as const };
  return (
    <Badge tone={entry.tone} className={cn("capitalize", className)}>
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full bg-current",
          entry.pulse && "animate-pulse-slow"
        )}
        aria-hidden
      />
      {entry.label}
    </Badge>
  );
}
