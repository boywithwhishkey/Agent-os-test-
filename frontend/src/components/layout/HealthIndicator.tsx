import { useHealth } from "@/lib/api/queries";
import { Tooltip } from "@/components/ui/Tooltip";
import { cn } from "@/lib/utils";

type ConnState = "online" | "connecting" | "offline";

const toneClass: Record<ConnState, string> = {
  online: "border-accent-green/25 bg-accent-green/10 text-accent-green",
  connecting: "border-accent-amber/25 bg-accent-amber/10 text-accent-amber",
  offline: "border-accent-red/25 bg-accent-red/10 text-accent-red",
};

const dotClass: Record<ConnState, string> = {
  online: "bg-accent-green",
  connecting: "bg-accent-amber",
  offline: "bg-accent-red",
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
          "inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium",
          toneClass[state]
        )}
      >
        {/* Fixed-size wrapper so the expanding ring never shifts layout. */}
        <span className="relative flex h-2 w-2 shrink-0 items-center justify-center" aria-hidden>
          {state === "online" && (
            <span className={cn("absolute h-2 w-2 rounded-full animate-heartbeat-ring", dotClass[state])} />
          )}
          <span
            className={cn(
              "relative h-2 w-2 rounded-full",
              dotClass[state],
              state === "online" && "animate-heartbeat",
              state === "connecting" && "animate-breathe",
              state === "offline" && "animate-pulse-slow"
            )}
          />
        </span>
        {label[state]}
      </span>
    </Tooltip>
  );
}
