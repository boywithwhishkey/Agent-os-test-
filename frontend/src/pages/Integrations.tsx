import { useEffect, useMemo, useState } from "react";
import { useT } from "@/lib/i18n";
import { useSearchParams } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import { Plug, Sparkles, Plus, Clock3 } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { SearchInput } from "@/components/ui/SearchInput";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { ScrollReveal } from "@/components/ui/ScrollReveal";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { ConnectorCard } from "@/components/integrations/ConnectorCard";
import { ConnectorDrawer } from "@/components/integrations/ConnectorDrawer";
import { AddMcpServerDialog } from "@/components/integrations/AddMcpServerDialog";
import { AuthRequiredBanner } from "@/components/integrations/AuthRequiredBanner";
import { Button } from "@/components/ui/Button";
import { useToast } from "@/components/ui/Toast";
import { useConnectorCatalog, useMCPServers, useTestIntegration, useTestMCPServer } from "@/lib/api/queries";
import { isApiConfigured } from "@/lib/api/config";
import {
  matchesFilter,
  matchesSearch,
  mcpServerToConnector,
  isConnected,
  isReadyToConnect,
  isComingSoon,
  type FilterChip,
  type UnifiedConnector,
} from "@/lib/integration-hub";
import { cn } from "@/lib/utils";

// `value` is the machine filter token and never changes; `labelKey` is what the
// user reads. Protocol names (MCP, API, OAuth, Webhook, AI) stay as-is — they
// are technical identifiers, not copy.
const FILTERS: { value: FilterChip; label?: string; labelKey?: string }[] = [
  { value: "all", labelKey: "pages.integrations.all" },
  { value: "connected", labelKey: "pages.integrations.connected" },
  { value: "ready", labelKey: "pages.integrations.readyToConnect" },
  { value: "coming_soon", labelKey: "pages.integrations.comingSoon" },
  { value: "mcp", label: "MCP" },
  { value: "api", label: "API" },
  { value: "oauth", label: "OAuth" },
  { value: "webhook", label: "Webhook" },
  { value: "ai", label: "AI" },
  { value: "automation", label: "Automation" },
  { value: "developer", label: "Developer" },
  { value: "productivity", label: "Productivity" },
  { value: "data", label: "Data" },
  { value: "google", label: "Google" },
];

export default function Integrations() {
  const t = useT();
  const catalog = useConnectorCatalog();
  const mcpServers = useMCPServers();
  const testIntegration = useTestIntegration();
  const testMcp = useTestMCPServer();
  const authed = isApiConfigured();
  const { push } = useToast();

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<FilterChip>("all");
  const [selected, setSelected] = useState<UnifiedConnector | null>(null);
  const [addMcpOpen, setAddMcpOpen] = useState(false);
  const [searchParams, setSearchParams] = useSearchParams();

  useEffect(() => {
    const oauthResult = searchParams.get("oauth");
    if (!oauthResult) return;
    const provider = searchParams.get("provider") ?? "the provider";
    if (oauthResult === "connected") {
      push({ tone: "success", title: `Connected to ${provider}` });
    } else {
      const message = searchParams.get("message") ?? "The authorization did not complete.";
      push({ tone: "error", title: `Could not connect to ${provider}`, description: message });
    }
    const next = new URLSearchParams(searchParams);
    next.delete("oauth");
    next.delete("provider");
    next.delete("message");
    setSearchParams(next, { replace: true });
    // Only re-run when the oauth redirect params themselves change.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchParams.get("oauth")]);

  const allConnectors: UnifiedConnector[] = useMemo(() => {
    const catalogItems: UnifiedConnector[] = catalog.data ?? [];
    const mcpItems = (mcpServers.data ?? []).map(mcpServerToConnector);
    return [...catalogItems, ...mcpItems];
  }, [catalog.data, mcpServers.data]);

  // A connector is always exactly one of these three states — never a mix
  // (see CLAUDE.md's Integration Hub product rule).
  const connected = useMemo(() => allConnectors.filter(isConnected), [allConnectors]);
  const readyToConnect = useMemo(() => allConnectors.filter(isReadyToConnect), [allConnectors]);
  const popular = useMemo(
    () => allConnectors.filter((c) => c.popular && (isConnected(c) || isReadyToConnect(c))),
    [allConnectors]
  );

  const filtered = useMemo(
    () => allConnectors.filter((c) => matchesSearch(c, search) && matchesFilter(c, filter)),
    [allConnectors, search, filter]
  );
  const filteredWorking = useMemo(() => filtered.filter((c) => !isComingSoon(c)), [filtered]);
  const filteredComingSoon = useMemo(() => filtered.filter(isComingSoon), [filtered]);

  const isLoading = catalog.isLoading || mcpServers.isLoading;
  const isError = catalog.isError;

  const testing = (connector: UnifiedConnector) =>
    connector.mcpServer ? testMcp.isPending && testMcp.variables === connector.mcpServer.id : testIntegration.isPending;

  const handleTest = (connector: UnifiedConnector) => {
    if (connector.mcpServer) testMcp.mutate(connector.mcpServer.id);
    else testIntegration.mutate(connector.id);
  };

  return (
    <div className="space-y-8">
      <PageHeader
        title={t("pages.integrations.title")}
        description={t("pages.integrations.description")}
        actions={
          <Button size="sm" onClick={() => setAddMcpOpen(true)} disabled={!authed}>
            <Plus className="h-3.5 w-3.5" /> {t("pages.integrations.addMcpServer")}
          </Button>
        }
      />

      {!authed && <AuthRequiredBanner />}

      {isError ? (
        <ErrorState error={catalog.error} onRetry={() => catalog.refetch()} />
      ) : (
        <>
          {/* Currently integrated — only real, verified connections. */}
          <section className="space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-content-muted">{t("pages.integrations.currentlyIntegrated")}</h2>
            {isLoading ? (
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                <SkeletonCard />
              </div>
            ) : connected.length === 0 ? (
              <EmptyState
                icon={<Plug className="h-5 w-5" />}
                title={t("pages.integrations.emptyTitle")}
                description={t("pages.integrations.emptyBody")}
              />
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                <AnimatePresence>
                  {connected.map((connector) => (
                    <ConnectorCard
                      key={connector.id}
                      connector={connector}
                      variant="integrated"
                      onSelect={() => setSelected(connector)}
                      onTest={() => handleTest(connector)}
                      testing={testing(connector)}
                    />
                  ))}
                </AnimatePresence>
              </div>
            )}
          </section>

          {/* Ready to connect — implementation-complete, only credentials/OAuth are missing. */}
          {!isLoading && readyToConnect.length > 0 && (
            <section className="space-y-3">
              <h2 className="flex items-center gap-1.5 text-sm font-semibold uppercase tracking-wide text-content-muted">
                <Clock3 className="h-3.5 w-3.5 text-accent-amber" /> {t("pages.integrations.readyToConnect")}
              </h2>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                <AnimatePresence>
                  {readyToConnect.map((connector) => (
                    <ConnectorCard
                      key={connector.id}
                      connector={connector}
                      onSelect={() => setSelected(connector)}
                      onTest={
                        connector.status === "configured" || connector.status === "error"
                          ? () => handleTest(connector)
                          : undefined
                      }
                      testing={testing(connector)}
                    />
                  ))}
                </AnimatePresence>
              </div>
            </section>
          )}

          {/* Popular */}
          {!isLoading && popular.length > 0 && (
            <section className="space-y-3">
              <h2 className="flex items-center gap-1.5 text-sm font-semibold uppercase tracking-wide text-content-muted">
                <Sparkles className="h-3.5 w-3.5 text-accent-gold" /> Popular integrations
              </h2>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {popular.map((connector) => (
                  <ConnectorCard key={connector.id} connector={connector} onSelect={() => setSelected(connector)} />
                ))}
              </div>
            </section>
          )}

          {/* All integrations */}
          <ScrollReveal>
          <section className="space-y-4">
            <div className="flex flex-col gap-3">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-content-muted">{t("common.allIntegrations")}</h2>
              <SearchInput value={search} onChange={setSearch} placeholder={t("pages.integrations.searchPlaceholder")} className="w-full sm:max-w-md" />
              <div className="-mx-1 flex gap-1.5 overflow-x-auto px-1 pb-1">
                {FILTERS.map((f) => (
                  <button
                    key={f.value}
                    onClick={() => setFilter(f.value)}
                    className={cn(
                      "shrink-0 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                      filter === f.value
                        ? "border-accent-gold/40 bg-accent-gold/10 text-accent-gold"
                        : "glass-ambient border-hairline text-content-muted hover:text-content-primary"
                    )}
                  >
                    {/* Translated chrome where we have a key; protocol names
                        (MCP, API, OAuth) keep their literal label. */}
                    {f.labelKey ? t(f.labelKey as Parameters<typeof t>[0]) : f.label}
                  </button>
                ))}
              </div>
            </div>

            {isLoading ? (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                <SkeletonCard />
                <SkeletonCard />
                <SkeletonCard />
              </div>
            ) : filtered.length === 0 ? (
              <EmptyState
                icon={<Plug className="h-5 w-5" />}
                title={t("pages.integrations.noMatchTitle")}
                description={t("pages.integrations.noMatchBody")}
              />
            ) : (
              <>
                {filteredWorking.length > 0 && (
                  <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                    <AnimatePresence>
                      {filteredWorking.map((connector) => (
                        <ConnectorCard key={connector.id} connector={connector} onSelect={() => setSelected(connector)} />
                      ))}
                    </AnimatePresence>
                  </div>
                )}

                {filteredComingSoon.length > 0 && (
                  <div className="space-y-3 border-t border-hairline pt-4">
                    <h3 className="text-xs font-semibold uppercase tracking-wide text-content-muted">
                      Coming soon — no adapter built yet
                    </h3>
                    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                      <AnimatePresence>
                        {filteredComingSoon.map((connector) => (
                          <ConnectorCard key={connector.id} connector={connector} onSelect={() => setSelected(connector)} />
                        ))}
                      </AnimatePresence>
                    </div>
                  </div>
                )}
              </>
            )}
            <p className="text-xs text-content-muted">
              Showing {filtered.length} of {allConnectors.length} integrations
            </p>
          </section>
          </ScrollReveal>
        </>
      )}

      <ConnectorDrawer connector={selected} open={Boolean(selected)} onClose={() => setSelected(null)} />
      <AddMcpServerDialog open={addMcpOpen} onClose={() => setAddMcpOpen(false)} />
    </div>
  );
}
