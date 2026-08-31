import { useHealth } from "@/lib/api/queries";
import { Tooltip } from "@/components/ui/Tooltip";
import { HeartbeatLine, type HeartbeatState } from "@/components/ui/HeartbeatLine";
import { cn } from "@/lib/utils";

type ConnState = HeartbeatState;

const toneClass: Record<ConnState, string> = {
  online: "text-accent-green",
  connecting: "text-accent-amber",
  offline: "text-accent-red",
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
          // No pill: the waveform and colour already carry the state, and a
          // filled capsule here read as one more box in a bar meant to be
          // chrome-less.
          "inline-flex items-center gap-1.5 px-1 py-1 text-xs font-medium sm:gap-2",
          toneClass[state]
        )}
      >
        <HeartbeatLine state={state} width={30} height={14} />
        <span className="hidden sm:inline">{label[state]}</span>
      </span>
    </Tooltip>
  );
}
