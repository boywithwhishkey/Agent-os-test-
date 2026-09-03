import { Link } from "react-router-dom";
import { KeyRound } from "lucide-react";
import { useHealth } from "@/lib/api/queries";
import { Tooltip } from "@/components/ui/Tooltip";
import { HeartbeatLine, type HeartbeatState } from "@/components/ui/HeartbeatLine";
import { isApiConfigured } from "@/lib/api/config";
import { cn } from "@/lib/utils";
import { useT } from "@/lib/i18n";

/**
 * One status control covering two INDEPENDENT axes:
 *
 *   reachability — can we talk to the API at all?
 *   authorisation — do we hold an operator key?
 *
 * These were previously two sibling chips, so a perfectly ordinary state
 * rendered as an amber "API key needed" warning immediately beside a green
 * "API Online" success. Both were true, but read together they looked
 * contradictory, and the amber implied something was broken when nothing was.
 *
 * Grouping them behind one divider makes it a single compound statement —
 * "reachable, and it needs a key" — rather than two verdicts disagreeing. The
 * key half is a link, because unlike the connection state it is something the
 * operator can act on.
 *
 * A degraded backend is reported as degraded rather than green: `status` and
 * `warnings` come from the real payload, so a deployment running without
 * durable storage cannot present itself as fully healthy.
 */
export function ConnectionStatus({ showLabels = false }: { showLabels?: boolean } = {}) {
  const t = useT();
  const { data, isError, isLoading } = useHealth();
  const configured = isApiConfigured();

  const reachable = Boolean(data) && !isError;
  const degraded =
    reachable && (data?.status !== "ok" || (data?.warnings?.length ?? 0) > 0);

  const state: HeartbeatState = isLoading
    ? "connecting"
    : reachable
      ? degraded
        ? "connecting"
        : "online"
      : "offline";

  const label = isLoading
    ? t("topbar.connecting")
    : !reachable
      ? t("topbar.apiOffline")
      : degraded
        ? t("topbar.degraded")
        : t("topbar.apiOnline");

  const tone =
    state === "online"
      ? "text-accent-green"
      : state === "connecting"
        ? "text-accent-amber"
        : "text-accent-red";

  const tooltip = isLoading
    ? t("topbar.checkingApi")
    : !reachable
      ? t("topbar.apiUnreachable")
      : [
          `${data?.service ?? "API"} · ${data?.environment ?? "unknown"}`,
          data?.persistence === "ephemeral"
            ? t("topbar.storageEphemeral")
            : null,
          ...(data?.warnings ?? []),
        ]
          .filter(Boolean)
          .join(" · ");

  return (
    <span className="inline-flex items-center gap-1.5 sm:gap-2">
      <Tooltip content={tooltip}>
        <span className={cn("inline-flex items-center gap-1.5 px-1 py-1 text-xs font-medium sm:gap-2", tone)}>
          <HeartbeatLine state={state} width={30} height={14} />
          <span className={showLabels ? "inline" : "hidden sm:inline"}>{label}</span>
        </span>
      </Tooltip>

      {/* Only meaningful once we know the API is actually there: telling
          someone to add a key while the host is unreachable sends them to fix
          the wrong thing. */}
      {reachable && !configured && (
        <>
          <span className={showLabels ? "h-3 w-px bg-hairline" : "hidden h-3 w-px bg-hairline sm:block"} aria-hidden />
          <Link
            to="/settings"
            className="focus-ring inline-flex items-center gap-1 rounded px-1 py-1 text-[11px] font-medium text-content-muted transition-colors duration-200 hover:text-accent-gold"
          >
            <KeyRound className="h-3 w-3" />
            <span className={showLabels ? "inline" : "hidden sm:inline"}>{t("topbar.keyNeeded")}</span>
          </Link>
        </>
      )}
    </span>
  );
}
