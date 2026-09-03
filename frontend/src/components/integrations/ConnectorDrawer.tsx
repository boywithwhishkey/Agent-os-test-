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
  LogIn,
} from "lucide-react";
import { Drawer } from "@/components/ui/Drawer";
import { Badge } from "@/components/ui/Badge";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Button } from "@/components/ui/Button";
import { Input, Label, Textarea, FieldError } from "@/components/ui/Input";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { JSONViewer } from "@/components/ui/JSONViewer";
import { getConnectorIcon } from "./connectorIcons";
import { useT } from "@/lib/i18n";
import { AuthRequiredBanner } from "./AuthRequiredBanner";
import {
  useExecuteIntegration,
  useTestIntegration,
  useTestMCPServer,
  useDeleteMCPServer,
  useOAuthAuthorize,
  useOAuthDisconnect,
} from "@/lib/api/queries";
import { useToast } from "@/components/ui/Toast";
import { isApiConfigured } from "@/lib/api/config";
import { ApiError } from "@/lib/api/client";
import { formatDateTime, formatRelativeTime } from "@/lib/utils";
import type { UnifiedConnector } from "@/lib/integration-hub";

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-hairline py-2 text-sm last:border-0">
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
          <li key={item.name} className="glass-ambient rounded-lg border border-hairline px-2.5 py-1.5 text-xs">
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
  const oauthAuthorize = useOAuthAuthorize();
  const oauthDisconnect = useOAuthDisconnect();
  const { push } = useToast();
  const authed = isApiConfigured();
  const t = useT();

  if (!connector) return null;
  const Icon = getConnectorIcon(connector.icon);
  const isMcp = Boolean(connector.mcpServer);
  const isOAuth = connector.connector_type === "oauth" && connector.implemented;

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
      setPayloadError(t("pages.integrations.detail.payloadInvalid"));
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

  const runAuthorize = () => {
    oauthAuthorize.mutate(connector.id, {
      onSuccess: (data) => {
        window.location.href = data.authorize_url;
      },
      onError: (error) => push({ tone: "error", title: "Authorize failed", description: (error as Error).message }),
    });
  };

  const confirmDisconnectOAuth = () => {
    oauthDisconnect.mutate(connector.id, {
      onSuccess: () => {
        push({ tone: "success", title: `${connector.name} disconnected` });
        setConfirmDelete(false);
        onClose();
      },
      onError: (error) => push({ tone: "error", title: "Disconnect failed", description: (error as Error).message }),
    });
  };

  const testing = isMcp ? testMcp.isPending : testIntegration.isPending;
  const testError = isMcp ? testMcp.error : testIntegration.error;

  return (
    <Drawer open={open} onClose={onClose} title={connector.name}>
      <div className="space-y-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-center gap-3">
            <span className="flex h-11 w-11 items-center justify-center rounded-xl border border-hairline bg-surface-hover text-accent-gold">
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
          <div className="rounded-lg border border-hairline bg-surface-hover p-3 text-sm text-content-secondary">
            {t("pages.integrations.detail.catalogOnly")}
          </div>
        ) : connector.status === "needs_setup" ? (
          <div className="rounded-lg border border-hairline bg-surface-hover p-3 text-sm text-content-secondary">
            {t("pages.integrations.detail.requiresSetupPrefix")}{" "}
            {connector.requires.map((name, i) => (
              <span key={name}>
                {i > 0 && ", "}
                <code className="font-mono text-xs">{name}</code>
              </span>
            ))}{" "}
            {t("pages.integrations.detail.requiresSetupSuffix")}
          </div>
        ) : null}

        <dl>
          <Row label={t("pages.integrations.detail.authType")}>
            <span className="capitalize">{connector.auth_type.replace("_", " ")}</span>
          </Row>
          {connector.implemented && (
            <>
              <Row label={t("pages.integrations.detail.lastCheck")}>
                <span className="inline-flex items-center gap-1">
                  <Clock className="h-3 w-3" /> {formatRelativeTime(connector.last_check)}
                </span>
              </Row>
              {connector.last_check_latency_ms != null && (
                <Row label={t("pages.integrations.detail.latency")}>
                  <span className="inline-flex items-center gap-1">
                    <Gauge className="h-3 w-3" /> {Math.round(connector.last_check_latency_ms)} ms
                  </span>
                </Row>
              )}
              {connector.last_check_error && (
                <Row label={t("pages.integrations.detail.lastError")}>
                  <span className="text-accent-red">{connector.last_check_error}</span>
                </Row>
              )}
              {!isMcp && (
                <Row label={t("pages.integrations.detail.lastExecution")}>
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
                    t("pages.integrations.detail.never")
                  )}
                </Row>
              )}
            </>
          )}
          {connector.documentation_url && (
            <Row label={t("pages.integrations.detail.docs")}>
              <a
                href={connector.documentation_url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-accent-gold hover:underline"
              >
                {new URL(connector.documentation_url).hostname} <ExternalLink className="h-3 w-3" />
              </a>
            </Row>
          )}
        </dl>

        {connector.capabilities.length > 0 && !isMcp && (
          <div>
            <p className="mb-1.5 text-xs font-semibold uppercase tracking-wide text-content-muted">
              {connector.implemented
                ? t("pages.integrations.detail.capabilities")
                : t("pages.integrations.detail.plannedCapabilities")}
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
                  <CapabilityGroup icon={Wrench} title={t("pages.integrations.detail.tools")} items={caps.tools} />
                  <CapabilityGroup icon={FileTextIcon} title={t("pages.integrations.detail.resources")} items={caps.resources} />
                  <CapabilityGroup icon={MessageCircle} title={t("pages.integrations.detail.prompts")} items={caps.prompts} />
                  {caps.tools.length === 0 && caps.resources.length === 0 && caps.prompts.length === 0 && (
                    <p className="text-xs text-content-muted">
                      {t("pages.integrations.detail.noCapabilitiesYet")}
                    </p>
                  )}
                </>
              );
            })()}
          </div>
        )}

        {connector.implemented && (
          <div className="flex flex-wrap gap-2 border-t border-hairline pt-4">
            {isOAuth && connector.status !== "connected" ? (
              <Button
                size="sm"
                onClick={runAuthorize}
                loading={oauthAuthorize.isPending}
                disabled={!authed || connector.status === "needs_setup"}
              >
                <LogIn className="h-3.5 w-3.5" /> {t("pages.integrations.actions.connect", { name: connector.name })}
              </Button>
            ) : (
              <Button size="sm" onClick={runTest} loading={testing} disabled={!authed || connector.status === "needs_setup"}>
                <PlayCircle className="h-3.5 w-3.5" /> {t("pages.integrations.actions.testConnection")}
              </Button>
            )}
            {(isMcp || (isOAuth && connector.status === "connected")) && (
              <Button size="sm" variant="danger" onClick={() => setConfirmDelete(true)} disabled={!authed}>
                <Trash2 className="h-3.5 w-3.5" /> {t("pages.integrations.actions.disconnect")}
              </Button>
            )}
          </div>
        )}
        {testError && (
          <p className="text-xs text-accent-red">
            {testError instanceof ApiError ? testError.detail : t("pages.integrations.actions.testFailed")}
          </p>
        )}

        {connector.id === "n8n" && connector.configured && (
          <div className="space-y-3 border-t border-hairline pt-4">
            <p className="text-xs font-semibold uppercase tracking-wide text-content-muted">{t("pages.integrations.detail.executeWorkflow")}</p>
            <div>
              <Label htmlFor="drawer-workflow">{t("pages.integrations.detail.webhookWorkflow")}</Label>
              <Input id="drawer-workflow" value={workflow} onChange={(e) => setWorkflow(e.target.value)} placeholder="deploy-notify" />
            </div>
            <div>
              <Label htmlFor="drawer-payload">{t("pages.integrations.detail.payloadJson")}</Label>
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
              <PlayCircle className="h-3.5 w-3.5" /> {t("pages.integrations.actions.execute")}
            </Button>
            {execute.data && (
              <>
                <div className="flex items-center gap-2">
                  <Badge tone={execute.data.success ? "green" : "red"}>{execute.data.success ? t("pages.integrations.detail.success") : t("pages.integrations.detail.failed")}</Badge>
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
        onConfirm={isOAuth ? confirmDisconnectOAuth : confirmRemoveMcp}
        title={
          isOAuth
            ? t("pages.integrations.detail.disconnectNamed", { name: connector.name })
            : t("pages.integrations.detail.disconnectMcp")
        }
        description={
          isOAuth
            ? t("pages.integrations.detail.disconnectOAuthBody")
            : t("pages.integrations.detail.disconnectMcpBody")
        }
        confirmLabel={t("pages.integrations.actions.disconnect")}
        danger
        loading={isOAuth ? oauthDisconnect.isPending : deleteMcp.isPending}
      />
    </Drawer>
  );
}
