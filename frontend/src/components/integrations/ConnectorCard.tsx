import { motion } from "framer-motion";
import { Clock, Gauge, Settings2, PlayCircle, LogIn, Sparkles as SparklesIcon } from "lucide-react";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { getConnectorIcon } from "./connectorIcons";
import { cn, formatRelativeTime } from "@/lib/utils";
import { isComingSoon, primaryAction, type UnifiedConnector } from "@/lib/integration-hub";

const typeBadgeTone: Record<string, "violet" | "blue" | "green" | "amber"> = {
  mcp: "violet",
  api: "blue",
  oauth: "green",
  webhook: "amber",
};

export function ConnectorCard({
  connector,
  variant = "grid",
  onSelect,
  onTest,
  testing,
}: {
  connector: UnifiedConnector;
  variant?: "grid" | "integrated";
  onSelect: () => void;
  onTest?: () => void;
  testing?: boolean;
}) {
  const Icon = getConnectorIcon(connector.icon);
  const isIntegrated = variant === "integrated";
  const comingSoon = isComingSoon(connector);
  const action = primaryAction(connector);
  const showTestButton = Boolean(onTest) && connector.implemented && connector.status !== "needs_setup";

  return (
    <motion.div
      layout
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
    >
      <Card
        className={cn(
          "group relative flex h-full flex-col overflow-hidden transition-all",
          comingSoon
            ? "cursor-default opacity-70 saturate-[0.4] hover:opacity-90"
            : "cursor-pointer hover:-translate-y-0.5 hover:border-accent-violet/40 hover:shadow-lg",
          connector.status === "connected" && "border-accent-green/25"
        )}
        onClick={onSelect}
      >
        <CardContent className="flex flex-1 flex-col gap-3 p-4">
          <div className="flex items-start justify-between gap-2">
            <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border border-hairline bg-surface-hover text-content-secondary transition-colors group-hover:border-accent-violet/30 group-hover:text-accent-violet">
              <Icon className="h-5 w-5" />
            </span>
            {comingSoon ? <Badge tone="neutral">Coming soon</Badge> : <StatusBadge status={connector.status} />}
          </div>

          <div className="min-w-0 flex-1">
            <h3 className="truncate text-sm font-semibold text-content-primary">{connector.name}</h3>
            <p className="mt-0.5 line-clamp-2 text-xs text-content-muted">{connector.description}</p>
          </div>

          <div className="flex flex-wrap items-center gap-1.5">
            <Badge tone={typeBadgeTone[connector.connector_type] ?? "violet"} className="uppercase tracking-wide">
              {connector.connector_type}
            </Badge>
            {!comingSoon &&
              connector.capabilities.slice(0, isIntegrated ? 1 : 2).map((cap) => (
                <Badge key={cap} tone="neutral">
                  {cap}
                </Badge>
              ))}
            {!comingSoon && connector.capabilities.length > (isIntegrated ? 1 : 2) && (
              <Badge tone="neutral">+{connector.capabilities.length - (isIntegrated ? 1 : 2)}</Badge>
            )}
          </div>

          {connector.last_check && (
            <dl className="grid grid-cols-2 gap-x-3 gap-y-1 border-t border-hairline pt-2.5 text-xs text-content-muted">
              <div className="flex items-center gap-1">
                <Clock className="h-3 w-3" /> {formatRelativeTime(connector.last_check)}
              </div>
              {connector.last_check_latency_ms != null && (
                <div className="flex items-center gap-1">
                  <Gauge className="h-3 w-3" /> {Math.round(connector.last_check_latency_ms)} ms
                </div>
              )}
            </dl>
          )}

          <div className="mt-auto flex flex-wrap gap-2 pt-1" onClick={(e) => e.stopPropagation()}>
            {showTestButton && (
              <Button variant="outline" size="sm" onClick={onTest} loading={testing}>
                <PlayCircle className="h-3.5 w-3.5" /> Test
              </Button>
            )}
            {action.kind === "manage" && (
              <Button variant="ghost" size="sm" onClick={onSelect}>
                <Settings2 className="h-3.5 w-3.5" /> Manage
              </Button>
            )}
            {action.kind === "connect" && (
              <Button variant="secondary" size="sm" onClick={onSelect}>
                <LogIn className="h-3.5 w-3.5" /> {action.label}
              </Button>
            )}
            {action.kind === "configure" && (
              <Button variant="secondary" size="sm" onClick={onSelect}>
                <Settings2 className="h-3.5 w-3.5" /> {action.label}
              </Button>
            )}
            {action.kind === "coming_soon" && (
              <Button variant="ghost" size="sm" onClick={onSelect}>
                <SparklesIcon className="h-3.5 w-3.5" /> Learn more
              </Button>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
