import { useState } from "react";
import { Plug, PlayCircle, Zap, CheckCircle2, XCircle, Clock } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label, Select, Textarea, FieldError } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ErrorState, LoadingState } from "@/components/ui/States";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { JSONViewer } from "@/components/ui/JSONViewer";
import { useExecuteIntegration, useIntegrations, useTestIntegration } from "@/lib/api/queries";
import { ApiError } from "@/lib/api/client";
import { formatRelativeTime } from "@/lib/utils";
import type { IntegrationStatus } from "@/lib/types";
import { cn } from "@/lib/utils";

const providerIcon: Record<string, typeof Plug> = {
  n8n: Zap,
};

function connectionStatus(status: IntegrationStatus): string {
  if (!status.configured) return "unconfigured";
  if (status.connected === null) return "pending";
  return status.connected ? "healthy" : "unavailable";
}

function ConnectorCard({ status }: { status: IntegrationStatus }) {
  const test = useTestIntegration();
  const Icon = providerIcon[status.provider] ?? Plug;
  const testResult = test.data ?? status;

  return (
    <Card className="relative overflow-hidden transition hover:border-accent-violet/30">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <span
            className={cn(
              "flex h-8 w-8 items-center justify-center rounded-lg border",
              status.configured
                ? "border-accent-violet/25 bg-accent-violet/10 text-accent-violet"
                : "border-surface bg-surface-hover text-content-muted"
            )}
          >
            <Icon className="h-4 w-4" />
          </span>
          <span className="capitalize">{status.name}</span>
        </CardTitle>
        <StatusBadge status={connectionStatus(status)} />
      </CardHeader>
      <CardContent className="space-y-3 text-sm">
        {!status.configured ? (
          <div className="rounded-lg border border-accent-amber/25 bg-accent-amber/5 p-3 text-content-secondary">
            Not configured. Set{" "}
            {status.requires.map((name, i) => (
              <span key={name}>
                {i > 0 && ", "}
                <code className="font-mono text-xs">{name}</code>
              </span>
            ))}{" "}
            on the backend to enable this connector.
          </div>
        ) : (
          <dl className="space-y-1.5">
            <Row label="Last check">
              <span className="inline-flex items-center gap-1">
                <Clock className="h-3 w-3 text-content-muted" />
                {formatRelativeTime(testResult.last_check)}
              </span>
            </Row>
            {testResult.last_check_latency_ms != null && (
              <Row label="Latency">{Math.round(testResult.last_check_latency_ms)} ms</Row>
            )}
            {testResult.last_check_error && (
              <Row label="Last error">
                <span className="text-accent-red">{testResult.last_check_error}</span>
              </Row>
            )}
            <Row label="Last execution">{formatRelativeTime(testResult.last_execution)}</Row>
            {testResult.last_execution_success != null && (
              <Row label="Last result">
                <span className={cn("inline-flex items-center gap-1", testResult.last_execution_success ? "text-accent-green" : "text-accent-red")}>
                  {testResult.last_execution_success ? (
                    <CheckCircle2 className="h-3.5 w-3.5" />
                  ) : (
                    <XCircle className="h-3.5 w-3.5" />
                  )}
                  {testResult.last_execution_success ? "Success" : "Failed"}
                </span>
              </Row>
            )}
          </dl>
        )}

        <Button
          variant="outline"
          size="sm"
          onClick={() => test.mutate(status.provider)}
          loading={test.isPending}
          disabled={!status.configured}
        >
          Test connection
        </Button>
        {test.isError && (
          <p className="text-xs text-accent-red">
            {test.error instanceof ApiError ? test.error.detail : "Test connection failed"}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between">
      <dt className="text-content-muted">{label}</dt>
      <dd className="text-content-primary">{children}</dd>
    </div>
  );
}

export default function Integrations() {
  const integrations = useIntegrations();
  const [provider, setProvider] = useState("n8n");
  const [workflow, setWorkflow] = useState("");
  const [payloadText, setPayloadText] = useState("{}");
  const [payloadError, setPayloadError] = useState<string | undefined>();
  const execute = useExecuteIntegration();

  const run = () => {
    let payload: Record<string, unknown> = {};
    try {
      payload = payloadText.trim() ? JSON.parse(payloadText) : {};
      setPayloadError(undefined);
    } catch {
      setPayloadError("Payload must be valid JSON");
      return;
    }
    execute.mutate({ provider, request: { workflow, payload } });
  };

  const unsupportedProvider = execute.error instanceof ApiError && execute.error.status === 400;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Integrations"
        description="Connector gallery for configured external providers. Currently supported: n8n webhooks."
      />

      {integrations.isLoading ? (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : integrations.isError ? (
        <ErrorState error={integrations.error} onRetry={() => integrations.refetch()} />
      ) : (
        <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
          {integrations.data?.map((status) => (
            <ConnectorCard key={status.provider} status={status} />
          ))}
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plug className="h-4 w-4 text-accent-violet" /> Execute action
            </CardTitle>
            <Badge tone="neutral">Manual test</Badge>
          </CardHeader>
          <CardContent className="space-y-3">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <Label htmlFor="provider">Provider</Label>
                <Select id="provider" value={provider} onChange={(e) => setProvider(e.target.value)}>
                  <option value="n8n">n8n</option>
                </Select>
              </div>
              <div>
                <Label htmlFor="workflow">Webhook workflow</Label>
                <Input id="workflow" value={workflow} onChange={(e) => setWorkflow(e.target.value)} placeholder="deploy-notify" />
              </div>
            </div>
            <div>
              <Label htmlFor="payload">Payload (JSON)</Label>
              <Textarea id="payload" value={payloadText} onChange={(e) => setPayloadText(e.target.value)} rows={5} className="font-mono text-xs" />
              <FieldError>{payloadError}</FieldError>
            </div>
            <Button onClick={run} loading={execute.isPending} disabled={!workflow}>
              <PlayCircle className="h-4 w-4" /> Execute
            </Button>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Result</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {execute.isPending && <LoadingState label="Running integration…" />}
            {execute.isError && unsupportedProvider && (
              <div className="rounded-lg border border-accent-amber/25 bg-accent-amber/5 p-3 text-sm text-content-secondary">
                The backend reported this provider isn't configured or supported. Check{" "}
                <code className="font-mono text-xs">N8N_BASE_URL</code> on the server.
              </div>
            )}
            {execute.isError && !unsupportedProvider && <ErrorState error={execute.error} onRetry={run} />}
            {!execute.data && !execute.isError && !execute.isPending && (
              <p className="text-sm text-content-muted">Run an integration to see its result here.</p>
            )}
            {execute.data && (
              <>
                <div className="flex items-center gap-2">
                  <Badge tone={execute.data.success ? "green" : "red"}>{execute.data.success ? "Success" : "Failed"}</Badge>
                  {execute.data.status_code && <Badge tone="neutral">HTTP {execute.data.status_code}</Badge>}
                </div>
                {execute.data.error && <p className="text-sm text-accent-red">{execute.data.error}</p>}
                <JSONViewer data={execute.data} collapsedByDefault={false} />
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
