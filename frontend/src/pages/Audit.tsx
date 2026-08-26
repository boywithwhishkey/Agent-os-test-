import { useMemo, useState } from "react";
import { ScrollText } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { SearchInput } from "@/components/ui/SearchInput";
import { Select } from "@/components/ui/Input";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Badge } from "@/components/ui/Badge";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { SkeletonRows } from "@/components/ui/Skeleton";
import { Drawer } from "@/components/ui/Drawer";
import { JSONViewer } from "@/components/ui/JSONViewer";
import { useToolAudit } from "@/lib/api/queries";
import { formatDateTime } from "@/lib/utils";
import type { ToolAuditEvent } from "@/lib/types";

export default function Audit() {
  const audit = useToolAudit();
  const [search, setSearch] = useState("");
  const [outcome, setOutcome] = useState<"all" | "success" | "failed">("all");
  const [selected, setSelected] = useState<ToolAuditEvent | null>(null);

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
          <div className="flex flex-1 gap-2 sm:justify-end">
            <SearchInput value={search} onChange={setSearch} placeholder="Filter by tool…" className="max-w-xs" />
            <Select value={outcome} onChange={(e) => setOutcome(e.target.value as typeof outcome)} className="w-36">
              <option value="all">All outcomes</option>
              <option value="success">Success</option>
              <option value="failed">Failed</option>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {audit.isLoading ? (
            <SkeletonRows rows={6} />
          ) : audit.isError ? (
            <ErrorState error={audit.error} onRetry={() => audit.refetch()} />
          ) : filtered.length === 0 ? (
            <EmptyState icon={<ScrollText className="h-5 w-5" />} title="No matching audit events" />
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full min-w-[560px] text-sm">
                <thead>
                  <tr className="border-b border-surface text-left text-xs uppercase tracking-wider text-content-muted">
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
                      className="cursor-pointer border-b border-surface last:border-0 hover:bg-surface-hover"
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
