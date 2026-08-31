import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { ScrollText, Table2, GanttChartSquare, CheckCircle2, XCircle, Copy } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { SearchInput } from "@/components/ui/SearchInput";
import { Select } from "@/components/ui/Input";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Badge } from "@/components/ui/Badge";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { SkeletonRows } from "@/components/ui/Skeleton";
import { Drawer } from "@/components/ui/Drawer";
import { Button } from "@/components/ui/Button";
import { JSONViewer } from "@/components/ui/JSONViewer";
import { useToolAudit } from "@/lib/api/queries";
import { cn, formatDateTime } from "@/lib/utils";
import type { ToolAuditEvent } from "@/lib/types";

function AuditTimeline({ events, onSelect }: { events: ToolAuditEvent[]; onSelect: (event: ToolAuditEvent) => void }) {
  return (
    <ol className="relative space-y-1 pl-6">
      <div className="absolute bottom-2 left-[7px] top-2 w-px bg-surface" aria-hidden />
      {events.map((event, i) => (
        <motion.li
          key={i}
          initial={{ opacity: 0, x: -6 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: Math.min(i, 12) * 0.02, duration: 0.2 }}
          className="relative"
        >
          <span
            className={cn(
              "absolute -left-6 top-1.5 flex h-3.5 w-3.5 items-center justify-center rounded-full border-2",
              event.success ? "border-accent-green bg-accent-green/20" : "border-accent-red bg-accent-red/20"
            )}
            aria-hidden
          />
          <button
            onClick={() => onSelect(event)}
            className="focus-ring flex w-full items-center justify-between gap-3 rounded-lg px-2 py-2 text-left hover:bg-surface-hover"
          >
            <span className="flex min-w-0 items-center gap-2">
              {event.success ? (
                <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-accent-green" />
              ) : (
                <XCircle className="h-3.5 w-3.5 shrink-0 text-accent-red" />
              )}
              <span className="truncate text-sm font-medium text-content-primary">{event.tool}</span>
              <span className="shrink-0 text-xs capitalize text-content-muted">{event.risk.replace("_", " ")}</span>
              {event.approval_required && <Badge tone="amber">Approval</Badge>}
            </span>
            <span className="shrink-0 text-xs text-content-muted">{formatDateTime(event.timestamp)}</span>
          </button>
        </motion.li>
      ))}
    </ol>
  );
}

export default function Audit() {
  const audit = useToolAudit();
  const [search, setSearch] = useState("");
  const [outcome, setOutcome] = useState<"all" | "success" | "failed">("all");
  const [selected, setSelected] = useState<ToolAuditEvent | null>(null);
  const [view, setView] = useState<"table" | "timeline">("table");

  const filtered = useMemo(() => {
    const events = [...(audit.data ?? [])].reverse();
    return events.filter((event) => {
      if (outcome === "success" && !event.success) return false;
      if (outcome === "failed" && event.success) return false;
      if (search && !event.tool.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [audit.data, search, outcome]);

  return (
    <div className="space-y-6">
      <PageHeader title="Audit Logs" description="Every tool execution and approval check, most recent first." />

      <Card>
        <CardHeader className="flex-col items-stretch gap-3 sm:flex-row sm:items-center">
          <CardTitle className="flex items-center gap-2">
            <ScrollText className="h-4 w-4 text-accent-violet" /> Events
          </CardTitle>
          <div className="flex flex-1 flex-wrap gap-2 sm:justify-end">
            <SearchInput value={search} onChange={setSearch} placeholder="Filter by tool…" className="max-w-xs" />
            <Select value={outcome} onChange={(e) => setOutcome(e.target.value as typeof outcome)} className="w-36">
              <option value="all">All outcomes</option>
              <option value="success">Success</option>
              <option value="failed">Failed</option>
            </Select>
            <div className="glass-ambient flex rounded-lg border border-hairline p-0.5">
              <button
                onClick={() => setView("table")}
                aria-label="Table view"
                className={cn(
                  "rounded-md p-1.5 transition-colors",
                  view === "table" ? "bg-accent-violet/10 text-accent-violet" : "text-content-muted hover:text-content-primary"
                )}
              >
                <Table2 className="h-4 w-4" />
              </button>
              <button
                onClick={() => setView("timeline")}
                aria-label="Timeline view"
                className={cn(
                  "rounded-md p-1.5 transition-colors",
                  view === "timeline" ? "bg-accent-violet/10 text-accent-violet" : "text-content-muted hover:text-content-primary"
                )}
              >
                <GanttChartSquare className="h-4 w-4" />
              </button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {audit.isLoading ? (
            <SkeletonRows rows={6} />
          ) : audit.isError ? (
            <ErrorState error={audit.error} onRetry={() => audit.refetch()} />
          ) : filtered.length === 0 ? (
            <EmptyState icon={<ScrollText className="h-5 w-5" />} title="No matching audit events" />
          ) : view === "timeline" ? (
            <AuditTimeline events={filtered} onSelect={setSelected} />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] text-sm">
                <thead>
                  <tr className="border-b border-hairline text-left text-xs uppercase tracking-wider text-content-muted">
                    <th className="py-2 pr-3 font-medium">Tool</th>
                    <th className="py-2 pr-3 font-medium">Risk</th>
                    <th className="py-2 pr-3 font-medium">Outcome</th>
                    <th className="py-2 pr-3 font-medium">Approval</th>
                    <th className="py-2 font-medium">When</th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map((event, i) => (
                    <tr
                      key={i}
                      onClick={() => setSelected(event)}
                      className="cursor-pointer border-b border-hairline last:border-0 hover:bg-surface-hover"
                    >
                      <td className="py-2.5 pr-3 font-medium text-content-primary">{event.tool}</td>
                      <td className="py-2.5 pr-3 capitalize text-content-muted">{event.risk.replace("_", " ")}</td>
                      <td className="py-2.5 pr-3">
                        <StatusBadge status={event.success ? "succeeded" : "failed"} />
                      </td>
                      <td className="py-2.5 pr-3">
                        {event.approval_required ? <Badge tone="amber">Required</Badge> : <span className="text-content-muted">—</span>}
                      </td>
                      <td className="py-2.5 text-content-muted">{formatDateTime(event.timestamp)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>

      <Drawer open={Boolean(selected)} onClose={() => setSelected(null)} title="Audit event">
        {selected && (
          <div className="space-y-4">
            <div>
              <p className="text-sm font-medium text-content-primary">{selected.tool}</p>
              <p className="text-xs text-content-muted">{formatDateTime(selected.timestamp)}</p>
            </div>
            <div className="flex flex-wrap gap-2">
              <StatusBadge status={selected.success ? "succeeded" : "failed"} />
              <Badge tone="neutral" className="capitalize">
                {selected.risk.replace("_", " ")}
              </Badge>
              {selected.approval_required && <Badge tone="amber">Approval required</Badge>}
            </div>
            {selected.correlation_id && (
              <div className="flex items-center justify-between gap-2 rounded-lg border border-hairline glass-ambient p-3">
                <div className="min-w-0">
                  <p className="text-xs uppercase tracking-wide text-content-muted">Correlation ID</p>
                  <p className="truncate font-mono text-xs text-content-primary">
                    {selected.correlation_id}
                  </p>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  aria-label="Copy correlation ID"
                  onClick={() => navigator.clipboard.writeText(selected.correlation_id ?? "")}
                >
                  <Copy className="h-3.5 w-3.5" />
                </Button>
              </div>
            )}
            {selected.error && (
              <div className="rounded-lg border border-accent-red/25 bg-accent-red/5 p-3 text-sm text-accent-red">
                {selected.error}
              </div>
            )}
            <JSONViewer data={selected} collapsedByDefault={false} />
          </div>
        )}
      </Drawer>
    </div>
  );
}
