import { Activity, AlertCircle } from "lucide-react";
import { useHealth } from "@/lib/api/queries";
import { Tooltip } from "@/components/ui/Tooltip";
import { cn } from "@/lib/utils";

export function HealthIndicator() {
  const { data, isError, isLoading } = useHealth();
  const healthy = Boolean(data) && !isError;

  return (
    <Tooltip
      content={
        isLoading
          ? "Checking API…"
          : healthy
            ? `${data?.service} · ${data?.environment}`
            : "API unreachable"
      }
    >
      <span
        className={cn(
          "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
          healthy
            ? "border-accent-green/25 bg-accent-green/10 text-accent-green"
            : "border-accent-red/25 bg-accent-red/10 text-accent-red"
        )}
      >
        {healthy ? (
          <Activity className="h-3 w-3 animate-pulse-slow" />
        ) : (
          <AlertCircle className="h-3 w-3" />
        )}
        {isLoading ? "Checking" : healthy ? "API Online" : "API Offline"}
      </span>
    </Tooltip>
  );
}
