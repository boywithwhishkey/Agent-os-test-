import { useState } from "react";
import { Plug, PlayCircle } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label, Select, Textarea, FieldError } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { ErrorState } from "@/components/ui/States";
import { JSONViewer } from "@/components/ui/JSONViewer";
import { useExecuteIntegration } from "@/lib/api/queries";
import { ApiError } from "@/lib/api/client";

export default function Integrations() {
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
        description="Invoke configured external providers. Currently supported: n8n webhooks."
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plug className="h-4 w-4 text-accent-violet" /> n8n
            </CardTitle>
            <Badge tone="neutral">Webhook provider</Badge>
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
            {execute.isError && unsupportedProvider && (
              <div className="rounded-lg border border-accent-amber/25 bg-accent-amber/5 p-3 text-sm text-content-secondary">
                The backend reported this provider isn't configured or supported. Check{" "}
                <code className="font-mono text-xs">N8N_BASE_URL</code> on the server.
              </div>
            )}
            {execute.isError && !unsupportedProvider && <ErrorState error={execute.error} onRetry={run} />}
            {!execute.data && !execute.isError && (
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
