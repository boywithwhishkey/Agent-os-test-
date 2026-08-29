import { useState } from "react";
import {
  PlayCircle,
  Trash2,
  ExternalLink,
  CheckCircle2,
  XCircle,
  Clock,
  Gauge,
  Wrench,
  FileText as FileTextIcon,
  MessageCircle,
} from "lucide-react";
import { Drawer } from "@/components/ui/Drawer";
import { Badge } from "@/components/ui/Badge";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { Input, Label, Textarea, FieldError } from "@/components/ui/Input";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { JSONViewer } from "@/components/ui/JSONViewer";
import { getConnectorIcon } from "./connectorIcons";
import { AuthRequiredBanner } from "./AuthRequiredBanner";
import { useExecuteIntegration, useTestIntegration, useTestMCPServer, useDeleteMCPServer } from "@/lib/api/queries";
import { useToast } from "@/components/ui/Toast";
import { isApiConfigured } from "@/lib/api/config";
import { ApiError } from "@/lib/api/client";
import { formatDateTime, formatRelativeTime } from "@/lib/utils";
import type { UnifiedConnector } from "@/lib/integration-hub";

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-surface py-2 text-sm last:border-0">
      <dt className="text-content-muted">{label}</dt>
      <dd className="text-right text-content-primary">{children}</dd>
    </div>
  );
}

function CapabilityGroup({ icon: Icon, title, items }: { icon: typeof Wrench; title: string; items: { name: string; description?: string | null }[] }) {
  if (items.length === 0) return null;
  return (
    <div>
      <p className="mb-1.5 flex items-center gap-1.5 text-xs font-semibold uppercase tracking-wide text-content-muted">
        <Icon className="h-3.5 w-3.5" /> {title} ({items.length})
      </p>
      <ul className="space-y-1">
        {items.map((item) => (
          <li key={item.name} className="rounded-lg border border-surface bg-surface-canvas px-2.5 py-1.5 text-xs">
            <span className="font-medium text-content-primary">{item.name}</span>
            {item.description && <span className="ml-1.5 text-content-muted">{item.description}</span>}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function ConnectorDrawer({
  connector,
  open,
  onClose,
}: {
  connector: UnifiedConnector | null;
  open: boolean;
  onClose: () => void;
}) {
  const [confirmDelete, setConfirmDelete] = useState(false);
  const [workflow, setWorkflow] = useState("");
  const [payloadText, setPayloadText] = useState("{}");
  const [payloadError, setPayloadError] = useState<string | undefined>();

  const testIntegration = useTestIntegration();
  const testMcp = useTestMCPServer();
  const deleteMcp = useDeleteMCPServer();
  const execute = useExecuteIntegration();
  const { push } = useToast();
  const authed = isApiConfigured();

  if (!connector) return null;
  const Icon = getConnectorIcon(connector.icon);
  const isMcp = Boolean(connector.mcpServer);

  const runTest = () => {
    if (isMcp && connector.mcpServer) {
      testMcp.mutate(connector.mcpServer.id, {
        onError: (error) => push({ tone: "error", title: "Test failed", description: (error as Error).message }),
      });
    } else if (connector.implemented) {
      testIntegration.mutate(connector.id, {
        onError: (error) => push({ tone: "error", title: "Test failed", description: (error as Error).message }),
      });
    }
  };

  const runExecute = () => {
    let payload: Record<string, unknown> = {};
    try {
      payload = payloadText.trim() ? JSON.parse(payloadText) : {};
      setPayloadError(undefined);
    } catch {
      setPayloadError("Payload must be valid JSON");
      return;
    }
    execute.mutate({ provider: connector.id, request: { workflow, payload } });
  };

  const confirmRemoveMcp = () => {
    if (!connector.mcpServer) return;
    deleteMcp.mutate(connector.mcpServer.id, {
      onSuccess: () => {
        push({ tone: "success", title: "MCP server removed" });
        setConfirmDelete(false);
        onClose();
      },
      onError: (error) => push({ tone: "error", title: "Remove failed", description: (error as Error).message }),
    });
  };

  const testing = isMcp ? testMcp.isPending : testIntegration.isPending;
  const testError = isMcp ? testMcp.error : testIntegration.error;

  return (
    <Drawer open={open} onClose={onClose} title={connector.name}>
      <div className="space-y-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl border border-surface bg-surface-hover text-accent-violet">
              <Icon className="h-5 w-5" />
            </span>
            <div>
              <p className="text-sm font-semibold text-content-primary">{connector.name}</p>
              <p className="text-xs capitalize text-content-muted">{connector.category} · {connector.connector_type}</p>
            </div>
          </div>
          <StatusBadge status={connector.status} />
        </div>

        <p className="text-sm text-content-secondary">{connector.description}</p>

        {!authed && <AuthRequiredBanner />}

        {!connector.implemented ? (
          <div className="rounded-lg border border-surface bg-surface-hover p-3 text-sm text-content-secondary">
            Catalog only — this connector isn't built yet. It describes what THYNACT could
            support; no credentials are collected and no connection is possible until it's
            implemented.
          </div>
        ) : connector.status === "needs_setup" ? (
          <div className="rounded-lg border border-surface bg-surface-hover p-3 text-sm text-content-secondary">
            Requires setup. This connector needs{" "}
            {connector.requires.map((name, i) => (
              <span key={name}>
                {i > 0 && ", "}
                <code className="font-mono text-xs">{name}</code>
              </span>
            ))}{" "}
            configured on the backend before it can connect.
          </div>
        ) : null}

        <dl>
          <Row label="Auth type">
            <span className="capitalize">{connector.auth_type.replace("_", " ")}</span>
          </Row>
          {connector.implemented && (
            <>
              <Row label="Last check">
                <span className="inline-flex items-center gap-1">
                  <Clock className="h-3 w-3" /> {formatRelativeTime(connector.last_check)}
                </span>
              </Row>
              {connector.last_check_latency_ms != null && (
                <Row label="Latency">
                  <span className="inline-flex items-center gap-1">
                    <Gauge className="h-3 w-3" /> {Math.round(connector.last_check_latency_ms)} ms
                  </span>
                </Row>
              )}
              {connector.last_check_error && (
                <Row label="Last error">
                  <span className="text-accent-red">{connector.last_check_error}</span>
                </Row>
              )}
              {!isMcp && (
                <Row label="Last execution">
                  {connector.last_execution ? (
                    <span className="inline-flex items-center gap-1">
                      {connector.last_execution_success ? (
                        <CheckCircle2 className="h-3.5 w-3.5 text-accent-green" />
                      ) : (
                        <XCircle className="h-3.5 w-3.5 text-accent-red" />
                      )}
                      {formatDateTime(connector.last_execution)}
                    </span>
                  ) : (
                    "Never"
                  )}
                </Row>
              )}
            </>
          )}
          {connector.documentation_url && (
            <Row label="Docs">
              <a
                href={connector.documentation_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-accent-violet hover:underline"
              >
                {new URL(connector.documentation_url).hostname} <ExternalLink className="h-3 w-3" />
              </a>
            </Row>
          )}
        </dl>

        {connector.capabilities.length > 0 && !isMcp && (
          <div>
            <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-content-muted">
              {connector.implemented ? "Capabilities" : "Planned capabilities"}
            </p>
            <div className="flex flex-wrap gap-1.5">
              {connector.capabilities.map((cap) => (
                <Badge key={cap} tone="neutral">
                  {cap}
                </Badge>
              ))}
            </div>
          </div>
        )}

        {isMcp && connector.mcpServer && (
          <div className="space-y-3">
            {(() => {
              const caps = connector.mcpServer.capabilities ?? { tools: [], resources: [], prompts: [] };
              return (
                <>
                  <CapabilityGroup icon={Wrench} title="Tools" items={caps.tools} />
                  <CapabilityGroup icon={FileTextIcon} title="Resources" items={caps.resources} />
                  <CapabilityGroup icon={MessageCircle} title="Prompts" items={caps.prompts} />
                  {caps.tools.length === 0 && caps.resources.length === 0 && caps.prompts.length === 0 && (
                    <p className="text-xs text-content-muted">
                      No capabilities discovered yet — run "Test connection" to refresh.
                    </p>
                  )}
                </>
              );
            })()}
          </div>
        )}

        {connector.implemented && (
          <div className="flex flex-wrap gap-2 border-t border-surface pt-4">
            <Button size="sm" onClick={runTest} loading={testing} disabled={!authed || connector.status === "needs_setup"}>
              <PlayCircle className="h-3.5 w-3.5" /> Test connection
            </Button>
            {isMcp && (
              <Button size="sm" variant="danger" onClick={() => setConfirmDelete(true)} disabled={!authed}>
                <Trash2 className="h-3.5 w-3.5" /> Disconnect
              </Button>
            )}
          </div>
        )}
        {testError && (
          <p className="text-xs text-accent-red">
            {testError instanceof ApiError ? testError.detail : "Test connection failed"}
          </p>
        )}

        {connector.id === "n8n" && connector.configured && (
          <div className="space-y-3 border-t border-surface pt-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-content-muted">Execute a workflow</p>
            <div>
              <Label htmlFor="drawer-workflow">Webhook workflow</Label>
              <Input id="drawer-workflow" value={workflow} onChange={(e) => setWorkflow(e.target.value)} placeholder="deploy-notify" />
            </div>
            <div>
              <Label htmlFor="drawer-payload">Payload (JSON)</Label>
              <Textarea
                id="drawer-payload"
                value={payloadText}
                onChange={(e) => setPayloadText(e.target.value)}
                rows={4}
                className="font-mono text-xs"
              />
              <FieldError>{payloadError}</FieldError>
            </div>
            <Button size="sm" onClick={runExecute} loading={execute.isPending} disabled={!authed || !workflow}>
              <PlayCircle className="h-3.5 w-3.5" /> Execute
            </Button>
            {execute.data && (
              <>
                <div className="flex items-center gap-2">
                  <Badge tone={execute.data.success ? "green" : "red"}>{execute.data.success ? "Success" : "Failed"}</Badge>
                  {execute.data.status_code && <Badge tone="neutral">HTTP {execute.data.status_code}</Badge>}
                </div>
                <JSONViewer data={execute.data} collapsedByDefault={false} />
              </>
            )}
          </div>
        )}
      </div>

      <ConfirmDialog
        open={confirmDelete}
        onClose={() => setConfirmDelete(false)}
        onConfirm={confirmRemoveMcp}
        title="Disconnect this MCP server?"
        description="This removes the server configuration. This cannot be undone."
        confirmLabel="Disconnect"
        danger
        loading={deleteMcp.isPending}
      />
    </Drawer>
  );
}
