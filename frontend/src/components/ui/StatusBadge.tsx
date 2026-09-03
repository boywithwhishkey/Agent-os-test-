import { Badge } from "./Badge";
import { useT } from "@/lib/i18n";
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
  | "degraded"
  | "connected"
  | "configured"
  | "needs_setup"
  | "available"
  | "error"
  | "disabled";

// Label text lives in the locale catalogue under `badges.<status>`; the
// machine status is the key and never changes.
const config: Record<StatusKind, { tone: "neutral" | "gold" | "green" | "red" | "amber"; pulse?: boolean }> = {
  pending: { tone: "neutral" },
  running: { tone: "gold", pulse: true },
  completed: { tone: "green" },
  succeeded: { tone: "green" },
  failed: { tone: "red" },
  rejected: { tone: "red" },
  paused: { tone: "amber" },
  skipped: { tone: "neutral" },
  waiting_approval: { tone: "amber", pulse: true },
  ok: { tone: "green" },
  healthy: { tone: "green" },
  unconfigured: { tone: "neutral" },
  unavailable: { tone: "red" },
  degraded: { tone: "amber" },
  connected: { tone: "green", pulse: true },
  configured: { tone: "gold" },
  needs_setup: { tone: "amber" },
  available: { tone: "neutral" },
  error: { tone: "red" },
  disabled: { tone: "neutral" },
};

export function StatusBadge({ status, className }: { status: string; className?: string }) {
  const t = useT();
  const entry = config[status as StatusKind] ?? { tone: "neutral" as const };
  // Unknown statuses fall back to the raw value rather than a missing key —
  // a new backend status shows through instead of vanishing.
  const label =
    status in config ? t(`badges.${status}` as Parameters<typeof t>[0]) : status;
  return (
    <Badge tone={entry.tone} className={cn("capitalize", className)}>
      <span
        className={cn(
          "h-1.5 w-1.5 rounded-full bg-current",
          entry.pulse && "animate-pulse-slow"
        )}
        aria-hidden
      />
      {label}
    </Badge>
  );
}
