import { useEffect, useMemo, useState } from "react";
import { useT } from "@/lib/i18n";
import { useSearchParams } from "react-router-dom";
import { AnimatePresence } from "framer-motion";
import { Plug, Plus, Clock3 } from "lucide-react";
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
  matchesSearch,
  mcpServerToConnector,
  isConnected,
  bucketCounts,
  groupByCategory,
  CATEGORY_ORDER,
  statusBucket,
  STATUS_BUCKETS,
  type StatusBucket,
  type UnifiedConnector,
} from "@/lib/integration-hub";
import type { ConnectorCategory } from "@/lib/types";
import { cn } from "@/lib/utils";

/**
 * One filter chip. Carries its own count so an operator can see what a filter
 * holds before spending a tap on it — a chip that leads to an empty grid is a
 * wasted interaction, and on mobile it is a wasted scroll back as well.
 */
function Chip({
  label,
  count,
  active,
  onClick,
}: {
  label: string;
  count: number;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      disabled={count === 0}
      aria-pressed={active}
      className={cn(
        "focus-ring flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1.5 text-xs font-medium transition-colors max-sm:h-9",
        count === 0 && "cursor-not-allowed opacity-40",
        active
          ? "border-accent-gold/40 bg-accent-gold/10 text-accent-gold"
          : "glass-ambient border-hairline text-content-muted hover:text-content-primary"
      )}
    >
      {label}
      <span className={cn("tabular-nums", active ? "text-accent-gold/70" : "text-content-muted/70")}>{count}</span>
    </button>
  );
}

export default function Integrations() {
  const t = useT();
  const catalog = useConnectorCatalog();
  const mcpServers = useMCPServers();
  const testIntegration = useTestIntegration();
  const testMcp = useTestMCPServer();
  const authed = isApiConfigured();
  const { push } = useToast();

  const [search, setSearch] = useState("");
  const [bucket, setBucket] = useState<StatusBucket | "all">("all");
  const [category, setCategory] = useState<ConnectorCategory | "all">("all");
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
  // Scoped to connectors whose credentials are already in place, so the
  // operator's next action here is one tap on Test. Everything else that is
  // built but unconfigured lives in the browse section below under "Needs
  // setup" — listing all of it twice was 13 duplicate cards of scrolling.
  const readyToConnect = useMemo(
    () => allConnectors.filter((c) => statusBucket(c) === "needs_verification"),
    [allConnectors]
  );
  // Marketplace browse state. Counts are computed against the OTHER axis'
  // current selection, so a chip's number is what that chip would actually
  // show — not a catalog-wide total that turns out to be empty once clicked.
  const searched = useMemo(() => allConnectors.filter((c) => matchesSearch(c, search)), [allConnectors, search]);

  const counts = useMemo(
    () => bucketCounts(searched.filter((c) => category === "all" || c.category === category)),
    [searched, category]
  );

  const categoryCounts = useMemo(() => {
    const out = new Map<ConnectorCategory, number>();
    for (const c of searched) {
      if (bucket !== "all" && statusBucket(c) !== bucket) continue;
      out.set(c.category, (out.get(c.category) ?? 0) + 1);
    }
    return out;
  }, [searched, bucket]);

  const filtered = useMemo(
    () =>
      searched.filter(
        (c) =>
          (bucket === "all" || statusBucket(c) === bucket) && (category === "all" || c.category === category)
      ),
    [searched, bucket, category]
  );

  const groups = useMemo(() => groupByCategory(filtered), [filtered]);

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
              <p className="text-sm text-content-secondary">
                {t("pages.integrations.buckets.needs_verification.hint")}
              </p>
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

          {/* Browse — the marketplace proper. Grouped by category rather than
              repeating the two sections above, and every group is drawn from
              the real registry: there are no cards here with nothing behind
              them. Status is a filter, and each bucket says plainly what it
              means. */}
          <ScrollReveal>
            <section className="space-y-4">
              <div className="space-y-1">
                <h2 className="text-sm font-semibold uppercase tracking-wide text-content-muted">
                  {t("pages.integrations.browseTitle")}
                </h2>
                <p className="max-w-2xl text-sm text-content-secondary">{t("pages.integrations.browseBody")}</p>
              </div>

              <SearchInput
                value={search}
                onChange={setSearch}
                placeholder={t("pages.integrations.searchPlaceholder")}
                className="w-full sm:max-w-md"
              />

              {/* Two axes, one row each. Protocol chips were removed:
                  connector_type is already in the search haystack, so typing
                  "oauth" filters by it — a third chip row cost more attention
                  on mobile than it bought. */}
              <div className="-mx-1 flex gap-1.5 overflow-x-auto px-1 pb-1">
                <Chip
                  label={t("pages.integrations.allStatuses")}
                  count={searched.filter((c) => category === "all" || c.category === category).length}
                  active={bucket === "all"}
                  onClick={() => setBucket("all")}
                />
                {STATUS_BUCKETS.map((b) => (
                  <Chip
                    key={b}
                    label={t(`pages.integrations.buckets.${b}.label` as Parameters<typeof t>[0])}
                    count={counts[b]}
                    active={bucket === b}
                    onClick={() => setBucket(b)}
                  />
                ))}
              </div>

              <div className="-mx-1 flex gap-1.5 overflow-x-auto px-1 pb-1">
                <Chip
                  label={t("pages.integrations.allCategories")}
                  count={[...categoryCounts.values()].reduce((a, b) => a + b, 0)}
                  active={category === "all"}
                  onClick={() => setCategory("all")}
                />
                {CATEGORY_ORDER.filter((cat) => (categoryCounts.get(cat) ?? 0) > 0).map((cat) => (
                  <Chip
                    key={cat}
                    label={t(`pages.integrations.categories.${cat}` as Parameters<typeof t>[0])}
                    count={categoryCounts.get(cat) ?? 0}
                    active={category === cat}
                    onClick={() => setCategory(cat)}
                  />
                ))}
              </div>

              {/* What the selected status actually means, in one line. The
                  honest states are only useful if the operator knows what they
                  claim — especially "not built yet", which must never read as
                  something they could turn on. */}
              {bucket !== "all" && (
                <p className="text-xs text-content-muted">
                  {t(`pages.integrations.buckets.${bucket}.hint` as Parameters<typeof t>[0])}
                </p>
              )}

              {isLoading ? (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                  <SkeletonCard />
                  <SkeletonCard />
                  <SkeletonCard />
                </div>
              ) : groups.length === 0 ? (
                <EmptyState
                  icon={<Plug className="h-5 w-5" />}
                  title={t("pages.integrations.noMatchTitle")}
                  description={t("pages.integrations.noMatchBody")}
                />
              ) : (
                <div className="space-y-6">
                  {groups.map((group) => (
                    <div key={group.category} className="space-y-3">
                      <h3 className="flex items-baseline gap-2 text-xs font-semibold uppercase tracking-wide text-content-muted">
                        {t(`pages.integrations.categories.${group.category}` as Parameters<typeof t>[0])}
                        <span className="tabular-nums text-content-muted/70">{group.connectors.length}</span>
                      </h3>
                      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
                        <AnimatePresence>
                          {group.connectors.map((connector) => (
                            <ConnectorCard
                              key={connector.id}
                              connector={connector}
                              onSelect={() => setSelected(connector)}
                            />
                          ))}
                        </AnimatePresence>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              <p className="text-xs text-content-muted">
                {t("pages.integrations.showingCount", {
                  shown: filtered.length,
                  total: allConnectors.length,
                })}
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
