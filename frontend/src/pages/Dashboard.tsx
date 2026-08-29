import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { Activity, Wrench, ScrollText, ListChecks, Workflow, Bot, ArrowUpRight } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { BrandMark } from "@/components/ui/BrandMark";
import { MetricCard } from "@/components/ui/MetricCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { EmptyState, LoadingState, ErrorState } from "@/components/ui/States";
import { useHealth, useReadiness, useTools, useToolAudit } from "@/lib/api/queries";
import { useSessionHistory } from "@/lib/session-history";
import { formatRelativeTime } from "@/lib/utils";

export default function Dashboard() {
  const health = useHealth();
  const readiness = useReadiness();
  const tools = useTools();
  const audit = useToolAudit();

  const tasks = useSessionHistory("task");
  const workflowRuns = useSessionHistory("workflow-run");
  const executions = useSessionHistory("runtime-execution");

  const recentAudit = [...(audit.data ?? [])].reverse().slice(0, 6);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Live status of the THYNACT platform and this session's activity."
      />

      <div className="relative overflow-hidden rounded-2xl border border-surface bg-gradient-to-br from-accent-violet/10 via-surface-raised to-accent-blue/5 px-5 py-4">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <BrandMark variant="full" />
          <p className="text-sm text-content-muted">From intelligence to execution.</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard
          label="API status"
          value={health.isLoading ? "…" : health.data ? "Online" : "Offline"}
          tone={health.data ? "green" : "red"}
          icon={<Activity className="h-4 w-4" />}
          hint={readiness.data ? `${readiness.data.status}` : undefined}
        />
        <MetricCard
          label="Tools available"
          value={tools.isLoading ? "…" : (tools.data?.length ?? "—")}
          tone="violet"
          icon={<Wrench className="h-4 w-4" />}
        />
        <MetricCard
          label="Audit events"
          value={audit.isLoading ? "…" : (audit.data?.length ?? "—")}
          tone="blue"
          icon={<ScrollText className="h-4 w-4" />}
        />
        <MetricCard
          label="This session"
          value={tasks.length + workflowRuns.length + executions.length}
          tone="amber"
          icon={<ListChecks className="h-4 w-4" />}
          hint="Tasks, runs & executions started here"
        />
      </div>

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>Recent audit activity</CardTitle>
            <Link to="/audit">
              <Button variant="ghost" size="sm">
                View all <ArrowUpRight className="h-3.5 w-3.5" />
              </Button>
            </Link>
          </CardHeader>
          <CardContent>
            {audit.isLoading ? (
              <LoadingState label="Loading audit events…" />
            ) : audit.isError ? (
              <ErrorState error={audit.error} onRetry={() => audit.refetch()} />
            ) : recentAudit.length === 0 ? (
              <EmptyState
                icon={<ScrollText className="h-5 w-5" />}
                title="No audit events yet"
                description="Tool executions and approval checks will show up here."
              />
            ) : (
              <ul className="divide-y divide-surface">
                {recentAudit.map((event, i) => (
                  <li key={i} className="flex items-center justify-between gap-3 py-2.5 text-sm">
                    <div className="min-w-0">
                      <p className="truncate font-medium text-content-primary">{event.tool}</p>
                      <p className="text-xs text-content-muted">{formatRelativeTime(event.timestamp)}</p>
                    </div>
                    <StatusBadge status={event.success ? "succeeded" : "failed"} />
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Quick actions</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            <QuickAction to="/orchestrate" icon={<Workflow className="h-4 w-4" />} label="Start orchestration" />
            <QuickAction to="/autonomous" icon={<Bot className="h-4 w-4" />} label="Run autonomous objective" />
            <QuickAction to="/tasks" icon={<ListChecks className="h-4 w-4" />} label="Create a task" />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Session activity</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-3">
          <SessionList title="Tasks" entries={tasks} to="/tasks" />
          <SessionList title="Workflow runs" entries={workflowRuns} to="/workflows/runs" />
          <SessionList title="Runtime executions" entries={executions} to="/runtime" />
        </CardContent>
      </Card>
    </div>
  );
}

function QuickAction({ to, icon, label }: { to: string; icon: ReactNode; label: string }) {
  return (
    <Link
      to={to}
      className="focus-ring flex items-center gap-2.5 rounded-lg border border-surface px-3 py-2.5 text-sm font-medium text-content-secondary transition-colors hover:border-accent-violet/30 hover:bg-accent-violet/5 hover:text-accent-violet"
    >
      {icon}
      {label}
    </Link>
  );
}

function SessionList({ title, entries, to }: { title: string; entries: { id: string; label: string; createdAt: string }[]; to: string }) {
  return (
    <div>
      <p className="mb-2 text-xs font-semibold uppercase tracking-wider text-content-muted">{title}</p>
      {entries.length === 0 ? (
        <p className="text-sm text-content-muted">Nothing yet this session.</p>
      ) : (
        <ul className="space-y-1.5">
          {entries.slice(0, 4).map((entry) => (
            <li key={entry.id} className="truncate text-sm text-content-secondary">
              {entry.label}
            </li>
          ))}
        </ul>
      )}
      <Link to={to} className="mt-2 inline-block text-xs font-medium text-accent-violet hover:underline">
        View
      </Link>
    </div>
  );
}
