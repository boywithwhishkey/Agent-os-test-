import { useMemo, useState } from "react";
import { AnimatePresence } from "framer-motion";
import { Plug, Sparkles, Plus } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { SearchInput } from "@/components/ui/SearchInput";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { SkeletonCard } from "@/components/ui/Skeleton";
import { ConnectorCard } from "@/components/integrations/ConnectorCard";
import { ConnectorDrawer } from "@/components/integrations/ConnectorDrawer";
import { AddMcpServerDialog } from "@/components/integrations/AddMcpServerDialog";
import { AuthRequiredBanner } from "@/components/integrations/AuthRequiredBanner";
import { Button } from "@/components/ui/Button";
import { useConnectorCatalog, useMCPServers, useTestIntegration, useTestMCPServer } from "@/lib/api/queries";
import { isApiConfigured } from "@/lib/api/config";
import {
  matchesFilter,
  matchesSearch,
  mcpServerToConnector,
  isCurrentlyIntegrated,
  type FilterChip,
  type UnifiedConnector,
} from "@/lib/integration-hub";
import { cn } from "@/lib/utils";

const FILTERS: { value: FilterChip; label: string }[] = [
  { value: "all", label: "All" },
  { value: "connected", label: "Connected" },
  { value: "mcp", label: "MCP" },
  { value: "api", label: "API" },
  { value: "automation", label: "Automation" },
  { value: "ai", label: "AI" },
  { value: "productivity", label: "Productivity" },
  { value: "developer", label: "Developer" },
  { value: "data", label: "Data" },
];

export default function Integrations() {
  const catalog = useConnectorCatalog();
  const mcpServers = useMCPServers();
  const testIntegration = useTestIntegration();
  const testMcp = useTestMCPServer();
  const authed = isApiConfigured();

  const [search, setSearch] = useState("");
  const [filter, setFilter] = useState<FilterChip>("all");
  const [selected, setSelected] = useState<UnifiedConnector | null>(null);
  const [addMcpOpen, setAddMcpOpen] = useState(false);

  const allConnectors: UnifiedConnector[] = useMemo(() => {
    const catalogItems: UnifiedConnector[] = catalog.data ?? [];
    const mcpItems = (mcpServers.data ?? []).map(mcpServerToConnector);
    return [...catalogItems, ...mcpItems];
  }, [catalog.data, mcpServers.data]);

  const integrated = useMemo(() => allConnectors.filter(isCurrentlyIntegrated), [allConnectors]);
  const popular = useMemo(() => allConnectors.filter((c) => c.popular), [allConnectors]);
  const filtered = useMemo(
    () => allConnectors.filter((c) => matchesSearch(c, search) && matchesFilter(c, filter)),
    [allConnectors, search, filter]
  );

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
        title="THYNACT Integrations"
        description="Connect intelligence to the tools that make things happen."
        actions={
          <Button size="sm" onClick={() => setAddMcpOpen(true)} disabled={!authed}>
            <Plus className="h-3.5 w-3.5" /> Add MCP server
          </Button>
        }
      />

      {!authed && <AuthRequiredBanner />}

      {isError ? (
        <ErrorState error={catalog.error} onRetry={() => catalog.refetch()} />
      ) : (
        <>
          {/* Currently integrated */}
          <section className="space-y-3">
            <h2 className="text-sm font-semibold uppercase tracking-wide text-content-muted">Currently integrated</h2>
            {isLoading ? (
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                <SkeletonCard />
              </div>
            ) : integrated.length === 0 ? (
              <EmptyState
                icon={<Plug className="h-5 w-5" />}
                title="No integrations connected yet."
                description="Configure a connector below or add an MCP server to get started."
              />
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
                <AnimatePresence>
                  {integrated.map((connector) => (
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

          {/* Popular */}
          {!isLoading && popular.length > 0 && (
            <section className="space-y-3">
              <h2 className="flex items-center gap-1.5 text-sm font-semibold uppercase tracking-wide text-content-muted">
                <Sparkles className="h-3.5 w-3.5 text-accent-violet" /> Popular integrations
              </h2>
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                {popular.map((connector) => (
                  <ConnectorCard key={connector.id} connector={connector} onSelect={() => setSelected(connector)} />
                ))}
              </div>
            </section>
          )}

          {/* All integrations */}
          <section className="space-y-4">
            <div className="flex flex-col gap-3">
              <h2 className="text-sm font-semibold uppercase tracking-wide text-content-muted">All integrations</h2>
              <SearchInput value={search} onChange={setSearch} placeholder="Search integrations…" className="w-full sm:max-w-md" />
              <div className="-mx-1 flex gap-1.5 overflow-x-auto px-1 pb-1">
                {FILTERS.map((f) => (
                  <button
                    key={f.value}
                    onClick={() => setFilter(f.value)}
                    className={cn(
                      "shrink-0 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors",
                      filter === f.value
                        ? "border-accent-violet/40 bg-accent-violet/10 text-accent-violet"
                        : "border-surface text-content-muted hover:text-content-primary"
                    )}
                  >
                    {f.label}
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
                title="No integrations match your search"
                description="Try a different term or clear the filters."
              />
            ) : (
              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                <AnimatePresence>
                  {filtered.map((connector) => (
                    <ConnectorCard key={connector.id} connector={connector} onSelect={() => setSelected(connector)} />
                  ))}
                </AnimatePresence>
              </div>
            )}
            <p className="text-xs text-content-muted">
              Showing {filtered.length} of {allConnectors.length} integrations
            </p>
          </section>
        </>
      )}

      <ConnectorDrawer connector={selected} open={Boolean(selected)} onClose={() => setSelected(null)} />
      <AddMcpServerDialog open={addMcpOpen} onClose={() => setAddMcpOpen(false)} />
    </div>
  );
}
