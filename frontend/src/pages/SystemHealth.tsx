import type { ReactNode } from "react";
import { HeartPulse, RefreshCw } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ErrorState } from "@/components/ui/States";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { useHealth, useReadiness } from "@/lib/api/queries";

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
    </div>
  );
}

function Row({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div className="flex items-center justify-between border-b border-surface py-2 text-sm last:border-0">
      <dt className="capitalize text-content-muted">{label}</dt>
      <dd className="text-content-primary">{children}</dd>
    </div>
  );
}
