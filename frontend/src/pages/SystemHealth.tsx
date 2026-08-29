import { motion } from "framer-motion";
import {
  HeartPulse,
  RefreshCw,
  Database,
  Layers,
  Brain,
  ListChecks,
  Workflow,
  Wrench,
  GitBranch,
} from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ErrorState } from "@/components/ui/States";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { useHealth, useReadiness } from "@/lib/api/queries";
import { cn } from "@/lib/utils";

const backendIcon: Record<string, typeof Database> = {
  memory: Database,
  task: ListChecks,
  workflow: Workflow,
  workflow_definition: GitBranch,
  runtime: Layers,
  tool: Wrench,
  queue: Layers,
};

const backendLabel: Record<string, string> = {
  memory: "Memory store",
  task: "Task store",
  workflow: "Workflow store",
  workflow_definition: "Workflow definitions",
  runtime: "Runtime store",
  tool: "Tool store",
  queue: "Job queue",
};

function BackendNode({ name, backend, index }: { name: string; backend: string; index: number }) {
  const Icon = backendIcon[name] ?? Database;
  const durable = backend !== "memory";
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.04, duration: 0.25 }}
      className="flex items-center gap-3 rounded-lg border border-surface bg-surface-canvas px-3 py-2.5"
    >
      <span
        className={cn(
          "flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
          durable ? "bg-accent-green/10 text-accent-green" : "bg-surface-hover text-content-muted"
        )}
      >
        <Icon className="h-4 w-4" />
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-content-primary">{backendLabel[name] ?? name}</p>
        <p className="text-xs capitalize text-content-muted">{backend}</p>
      </div>
      <Badge tone={durable ? "green" : "amber"}>{durable ? "Durable" : "Ephemeral"}</Badge>
    </motion.div>
  );
}

export default function SystemHealth() {
  const health = useHealth();
  const readiness = useReadiness();

  return (
    <div className="space-y-6">
      <PageHeader
        title="System Health"
        description="Live status straight from the backend's /health and /ready endpoints."
        actions={
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              health.refetch();
              readiness.refetch();
            }}
          >
            <RefreshCw className="h-3.5 w-3.5" /> Refresh
          </Button>
        }
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <HeartPulse className="h-4 w-4 text-accent-violet" /> API service
            </CardTitle>
          </CardHeader>
          <CardContent>
            {health.isLoading ? (
              <SkeletonCard />
            ) : health.isError ? (
              <ErrorState error={health.error} onRetry={() => health.refetch()} />
            ) : (
              <dl className="space-y-2 text-sm">
                <Row label="Status">
                  <StatusBadge status={health.data?.status === "ok" ? "healthy" : "degraded"} />
                </Row>
                <Row label="Service">{health.data?.service}</Row>
                <Row label="Environment">{health.data?.environment}</Row>
                <Row label="LLM provider">
                  <Badge tone={health.data?.llm_provider === "mock" ? "amber" : "violet"} className="capitalize">
                    <Brain className="h-3 w-3" /> {health.data?.llm_provider}
                  </Badge>
                </Row>
              </dl>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <HeartPulse className="h-4 w-4 text-accent-violet" /> Readiness checks
            </CardTitle>
          </CardHeader>
          <CardContent>
            {readiness.isLoading ? (
              <SkeletonCard />
            ) : readiness.isError ? (
              <ErrorState error={readiness.error} onRetry={() => readiness.refetch()} />
            ) : (
              <div className="space-y-3">
                <Row label="Overall">
                  <StatusBadge status={readiness.data?.status === "ready" ? "healthy" : "degraded"} />
                </Row>
                {Object.entries(readiness.data?.checks ?? {}).length === 0 ? (
                  <p className="text-sm text-content-muted">
                    No dependency checks are active — no Postgres/Redis-backed features are configured for this deployment.
                  </p>
                ) : (
                  Object.entries(readiness.data?.checks ?? {}).map(([name, status]) => (
                    <Row key={name} label={name}>
                      <StatusBadge status={status} />
                    </Row>
                  ))
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-accent-violet" /> Persistence map
          </CardTitle>
        </CardHeader>
        <CardContent>
          {health.isLoading ? (
            <SkeletonCard />
          ) : health.isError || !health.data ? (
            <p className="text-sm text-content-muted">Unavailable — the API is unreachable.</p>
          ) : (
            <div className="grid gap-2.5 sm:grid-cols-2 lg:grid-cols-3">
              {Object.entries(health.data.backends).map(([name, backend], i) => (
                <BackendNode key={name} name={name} backend={backend} index={i} />
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-surface py-2 text-sm last:border-0">
      <dt className="capitalize text-content-muted">{label}</dt>
      <dd className="text-content-primary">{children}</dd>
    </div>
  );
}
