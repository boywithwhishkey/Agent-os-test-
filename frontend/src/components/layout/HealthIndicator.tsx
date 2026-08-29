import { useHealth } from "@/lib/api/queries";
import { Tooltip } from "@/components/ui/Tooltip";
import { HeartbeatLine, type HeartbeatState } from "@/components/ui/HeartbeatLine";
import { cn } from "@/lib/utils";

type ConnState = HeartbeatState;

const toneClass: Record<ConnState, string> = {
  online: "border-accent-green/25 bg-accent-green/10 text-accent-green",
  connecting: "border-accent-amber/25 bg-accent-amber/10 text-accent-amber",
  offline: "border-accent-red/25 bg-accent-red/10 text-accent-red",
};

const label: Record<ConnState, string> = {
  online: "API Online",
  connecting: "Connecting",
  offline: "API Offline",
};

export function HealthIndicator() {
  const { data, isError, isLoading } = useHealth();
  const state: ConnState = isLoading ? "connecting" : data && !isError ? "online" : "offline";

  const tooltip =
    state === "connecting"
      ? "Checking API…"
      : state === "online"
        ? `${data?.service} · ${data?.environment}`
        : "API unreachable";

  return (
    <Tooltip content={tooltip}>
      <span
        className={cn(
          "inline-flex items-center gap-2 rounded-full border pl-2 pr-2.5 py-1 text-xs font-medium",
          toneClass[state]
        )}
      >
        <HeartbeatLine state={state} width={36} height={14} />
        {label[state]}
      </span>
    </Tooltip>
  );
}
