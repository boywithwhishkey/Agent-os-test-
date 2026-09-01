import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { Activity, Wrench, ScrollText, ListChecks, Workflow, Bot, ArrowUpRight } from "lucide-react";
import { BrandMark } from "@/components/ui/BrandMark";
import { MetricCard } from "@/components/ui/MetricCard";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { EmptyState, LoadingState, ErrorState } from "@/components/ui/States";
import { ScrollReveal, StaggerGroup, StaggerItem } from "@/components/ui/ScrollReveal";
import { HeartbeatLine } from "@/components/ui/HeartbeatLine";
import { staggerContainer, staggerItem } from "@/lib/motion";
import { useHealth, useReadiness, useTools, useToolAudit } from "@/lib/api/queries";
import { ApiError } from "@/lib/api/client";
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

  /**
   * A metric that failed to load is not the same as a metric that is zero, and
   * neither is an em dash. These cards previously rendered "—" for both, which
   * silently turned "you are not signed in" into what looked like "no data" —
   * the operator had no way to know there was an action to take.
   *
   * 0 is a real, meaningful value and must render as 0, so the count is only
   * substituted when it is genuinely absent.
   */
  const metricValue = (q: { isLoading: boolean; isError: boolean; error: unknown; data?: unknown[] }) => {
    if (q.isLoading) return "…";
    if (q.isError) {
      const err = q.error;
      if (err instanceof ApiError) {
        if (err.isUnauthorized) return "Sign in";
        if (err.isNetworkError || err.isTimeout) return "Offline";
      }
      return "Unavailable";
    }
    return q.data?.length ?? 0;
  };

  /** Unavailable/auth values are words, not figures — don't style them as data. */
  const metricTone = (q: { isError: boolean }) => (q.isError ? "amber" : "neutral");

  // Reachable is not the same as healthy: a backend running without durable
  // storage, or reporting warnings, must not present itself as plain green.
  const apiDegraded =
    Boolean(health.data) &&
    (health.data?.status !== "ok" ||
      (health.data?.warnings?.length ?? 0) > 0 ||
      health.data?.persistence === "ephemeral");

  return (
    <div className="space-y-10">
      {/* System identity — deliberately not a bordered card. It emerges
          straight out of the ambient canvas behind the app shell. */}
      <div className="relative -mx-4 overflow-hidden px-4 py-7 sm:-mx-6 sm:px-6 sm:py-10 lg:-mx-8 lg:px-8">
        <div className="pointer-events-none absolute left-1/2 top-0 h-64 w-[36rem] -translate-x-1/2 rounded-full bg-ambient-gold/[0.14] blur-[100px] animate-float" aria-hidden />
        <div className="relative overflow-hidden">
          <span className="pointer-events-none absolute inset-x-0 top-0 h-px animate-scan bg-gradient-to-r from-transparent via-ambient-navy/60 to-transparent" aria-hidden />
          <motion.div
            initial="hidden"
            animate="visible"
            variants={staggerContainer}
            className="relative"
          >
            <motion.div variants={staggerItem}>
              <BrandMark variant="full" size="lg" />
            </motion.div>
          </motion.div>
        </div>
      </div>

      <StaggerGroup className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <StaggerItem className="h-full">
          <MetricCard
            label="API status"
            value={health.isLoading ? "…" : !health.data ? "Offline" : apiDegraded ? "Degraded" : "Online"}
            tone={!health.data ? "red" : apiDegraded ? "amber" : "green"}
            icon={<Activity className="h-4 w-4" />}
            hint={
              health.data
                ? health.data.persistence === "ephemeral"
                  ? "Ephemeral storage — data is lost on restart"
                  : (readiness.data?.status ?? undefined)
                : undefined
            }
            graphic={
              <HeartbeatLine state={health.isLoading ? "connecting" : health.data ? "online" : "offline"} width={72} height={18} />
            }
          />
        </StaggerItem>
        <StaggerItem className="h-full">
          <MetricCard
            label="Tools available"
            value={metricValue(tools)}
            tone={metricTone(tools)}
            icon={<Wrench className="h-4 w-4" />}
            hint={tools.isError ? "Operator key required to list tools" : undefined}
          />
        </StaggerItem>
        <StaggerItem className="h-full">
          <MetricCard
            label="Audit events"
            value={metricValue(audit)}
            tone={metricTone(audit)}
            icon={<ScrollText className="h-4 w-4" />}
            hint={audit.isError ? "Operator key required to read the audit log" : undefined}
          />
        </StaggerItem>
        <StaggerItem className="h-full">
          <MetricCard
            label="This session"
            value={tasks.length + workflowRuns.length + executions.length}
            tone="amber"
            icon={<ListChecks className="h-4 w-4" />}
            hint="Tasks, runs & executions started here"
          />
        </StaggerItem>
      </StaggerGroup>

      <ScrollReveal className="grid grid-cols-1 gap-4 lg:grid-cols-3">
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
              <ul className="divide-y divide-white/5">
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
      </ScrollReveal>

      <ScrollReveal delay={0.05}>
        <Card>
          <CardHeader>
            <CardTitle>Session activity</CardTitle>
          </CardHeader>
          <CardContent className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <SessionList title="Tasks" entries={tasks} to="/tasks" />
            <SessionList title="Workflow runs" entries={workflowRuns} to="/workflows/runs" />
            <SessionList title="Runtime executions" entries={executions} to="/runtime" />
          </CardContent>
        </Card>
      </ScrollReveal>
    </div>
  );
}

function QuickAction({ to, icon, label }: { to: string; icon: ReactNode; label: string }) {
  return (
    <Link
      to={to}
      className="focus-ring flex items-center gap-2.5 rounded-lg border border-hairline px-3 py-2.5 text-sm font-medium text-content-secondary transition-colors hover:border-accent-gold/30 hover:bg-accent-gold/5 hover:text-accent-gold"
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
      <Link to={to} className="mt-2 inline-block text-xs font-medium text-accent-gold hover:underline">
        View
      </Link>
    </div>
  );
}
