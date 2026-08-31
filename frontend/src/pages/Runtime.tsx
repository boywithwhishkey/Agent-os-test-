import { useState } from "react";
import { Server, PlayCircle, Search, ShieldCheck, ShieldAlert, Gauge } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label, Textarea, FieldError } from "@/components/ui/Input";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ErrorState, EmptyState } from "@/components/ui/States";
import { SkeletonRows } from "@/components/ui/Skeleton";
import { JSONViewer } from "@/components/ui/JSONViewer";
import { useExecuteRuntime, useRuntimeExecution, useRuntimeStatus } from "@/lib/api/queries";
import { useSessionHistory, recordHistory } from "@/lib/session-history";
import { useToast } from "@/components/ui/Toast";
import { cn, formatDateTime } from "@/lib/utils";
import type { RuntimeStatus } from "@/lib/types";

export default function Runtime() {
  const [provider, setProvider] = useState("n8n");
  const [workflow, setWorkflow] = useState("");
  const [payloadText, setPayloadText] = useState("{}");
  const [payloadError, setPayloadError] = useState<string | undefined>();
  const [idempotencyKey, setIdempotencyKey] = useState("");
  const [lookupId, setLookupId] = useState("");
  const [activeLookup, setActiveLookup] = useState<string | undefined>();

  const execute = useExecuteRuntime();
  const history = useSessionHistory("runtime-execution");
  const { push } = useToast();

  const run = () => {
    let payload: Record<string, unknown> = {};
    try {
      payload = payloadText.trim() ? JSON.parse(payloadText) : {};
      setPayloadError(undefined);
    } catch {
      setPayloadError("Payload must be valid JSON");
      return;
    }
    execute.mutate(
      { provider, workflow, payload, idempotency_key: idempotencyKey || null },
      {
        onSuccess: (execution) => {
          recordHistory("runtime-execution", {
            id: execution.id,
            label: `${execution.provider} · ${execution.workflow}`,
            createdAt: execution.created_at,
          });
          setActiveLookup(execution.id);
          push({ tone: "success", title: "Execution triggered", description: execution.id });
        },
        onError: (error) => push({ tone: "error", title: "Execution failed", description: (error as Error).message }),
      }
    );
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Runtime"
        description="Execute provider-backed workflows with retries, idempotency, and correlation tracking."
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <PlayCircle className="h-4 w-4 text-accent-gold" /> Execute
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
              <div>
                <Label htmlFor="provider">Provider</Label>
                <Input id="provider" value={provider} onChange={(e) => setProvider(e.target.value)} />
              </div>
              <div>
                <Label htmlFor="workflow">Workflow</Label>
                <Input id="workflow" value={workflow} onChange={(e) => setWorkflow(e.target.value)} placeholder="notify-team" />
              </div>
            </div>
            <div>
              <Label htmlFor="idempotency">Idempotency key (optional)</Label>
              <Input id="idempotency" value={idempotencyKey} onChange={(e) => setIdempotencyKey(e.target.value)} />
            </div>
            <div>
              <Label htmlFor="payload">Payload (JSON)</Label>
              <Textarea id="payload" value={payloadText} onChange={(e) => setPayloadText(e.target.value)} rows={4} className="font-mono text-xs" />
              <FieldError>{payloadError}</FieldError>
            </div>
            <Button onClick={run} loading={execute.isPending} disabled={!workflow}>
              Execute
            </Button>
            {execute.isError && <ErrorState error={execute.error} onRetry={run} />}
            {provider && workflow && <RuntimeGauges provider={provider} workflow={workflow} />}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-4 w-4 text-accent-gold" /> Inspect execution
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                value={lookupId}
                onChange={(e) => setLookupId(e.target.value)}
                placeholder="Paste an execution ID"
                onKeyDown={(e) => e.key === "Enter" && setActiveLookup(lookupId)}
              />
              <Button variant="secondary" onClick={() => setActiveLookup(lookupId)}>
                Look up
              </Button>
            </div>
            <ExecutionLookup executionId={activeLookup} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Server className="h-4 w-4 text-accent-gold" /> This session's executions
          </CardTitle>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <EmptyState title="No executions triggered yet" />
          ) : (
            <ul className="divide-y divide-surface">
              {history.map((entry) => (
                <li key={entry.id} className="flex items-center justify-between gap-3 py-2.5">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-content-primary">{entry.label}</p>
                    <p className="font-mono text-xs text-content-muted">{entry.id}</p>
                  </div>
                  <Button size="sm" variant="ghost" onClick={() => setActiveLookup(entry.id)}>
                    View
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function ExecutionLookup({ executionId }: { executionId: string | undefined }) {
  const { data, isLoading, isError, error, refetch } = useRuntimeExecution(executionId);
  if (!executionId) return <p className="text-sm text-content-muted">Enter an execution ID to inspect it.</p>;
  if (isLoading) return <SkeletonRows rows={3} />;
  if (isError) return <ErrorState error={error} onRetry={() => refetch()} />;
  if (!data) return null;

  return (
    <div className="space-y-3 glass-ambient rounded-lg border border-hairline p-4">
      <div className="flex items-center justify-between">
        <StatusBadge status={data.status} />
        <span className="text-xs text-content-muted">{data.attempts} attempts</span>
      </div>
      <dl className="grid grid-cols-1 gap-2 text-xs text-content-muted sm:grid-cols-2">
        <div>
          <dt className="font-medium">Correlation ID</dt>
          <dd className="truncate font-mono">{data.correlation_id ?? "—"}</dd>
        </div>
        <div>
          <dt className="font-medium">Idempotency key</dt>
          <dd className="truncate font-mono">{data.idempotency_key ?? "—"}</dd>
        </div>
        <div>
          <dt className="font-medium">Created</dt>
          <dd>{formatDateTime(data.created_at)}</dd>
        </div>
        <div>
          <dt className="font-medium">Updated</dt>
          <dd>{formatDateTime(data.updated_at)}</dd>
        </div>
      </dl>
      {data.error && <p className="text-sm text-accent-red">{data.error}</p>}
      <JSONViewer data={data.data} />
    </div>
  );
}

function RuntimeGauges({ provider, workflow }: { provider: string; workflow: string }) {
  const { data, isLoading } = useRuntimeStatus(provider, workflow);
  if (isLoading || !data) return null;
  return <RuntimeGaugesDisplay data={data} />;
}

function RuntimeGaugesDisplay({ data }: { data: RuntimeStatus }) {
  const { circuit_breaker: breaker, rate_limit: rateLimit } = data;
  const isOpen = breaker.state === "open";
  const usagePct = Math.min(100, Math.round((rateLimit.used / Math.max(1, rateLimit.limit)) * 100));
  const gaugeTone = usagePct >= 90 ? "bg-accent-red" : usagePct >= 60 ? "bg-accent-amber" : "bg-accent-green";

  return (
    <div className="grid gap-3 glass-ambient rounded-lg border border-hairline p-3 sm:grid-cols-2">
      <div className="space-y-1.5">
        <p className="flex items-center gap-1.5 text-xs font-medium text-content-muted">
          {isOpen ? <ShieldAlert className="h-3.5 w-3.5 text-accent-red" /> : <ShieldCheck className="h-3.5 w-3.5 text-accent-green" />}
          Circuit breaker
        </p>
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "inline-flex items-center gap-1 rounded-full border px-2 py-0.5 text-xs font-medium capitalize",
              isOpen
                ? "border-accent-red/25 bg-accent-red/10 text-accent-red animate-pulse-slow"
                : "border-accent-green/25 bg-accent-green/10 text-accent-green"
            )}
          >
            {breaker.state}
          </span>
          {isOpen && breaker.recovers_in_seconds != null && (
            <span className="text-xs text-content-muted">recovers in {Math.ceil(breaker.recovers_in_seconds)}s</span>
          )}
          {!isOpen && breaker.failures > 0 && (
            <span className="text-xs text-content-muted">{breaker.failures} recent failure(s)</span>
          )}
        </div>
      </div>

      <div className="space-y-1.5">
        <p className="flex items-center gap-1.5 text-xs font-medium text-content-muted">
          <Gauge className="h-3.5 w-3.5 text-accent-gold" /> Rate limit
        </p>
        <div className="h-1.5 w-full overflow-hidden rounded-full bg-surface">
          <div
            className={cn("h-full rounded-full transition-[width] duration-500", gaugeTone)}
            style={{ width: `${usagePct}%` }}
          />
        </div>
        <p className="text-xs text-content-muted">
          {rateLimit.used}/{rateLimit.limit} in {rateLimit.window_seconds}s
        </p>
      </div>
    </div>
  );
}
