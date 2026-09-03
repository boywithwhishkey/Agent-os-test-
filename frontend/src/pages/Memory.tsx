import { useState } from "react";
import { useT } from "@/lib/i18n";
import { motion, AnimatePresence } from "framer-motion";
import { Brain, Trash2, Search as SearchIcon, PenLine, List, Share2 } from "lucide-react";
import { MemoryGraph } from "@/components/memory/MemoryGraph";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label, Select, Textarea } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/Tabs";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { SkeletonRows } from "@/components/ui/Skeleton";
import { ConfirmDialog } from "@/components/ui/ConfirmDialog";
import { useMemorySearch, useWriteMemory, useDeleteMemory } from "@/lib/api/queries";
import { useToast } from "@/components/ui/Toast";
import { formatDateTime, truncate } from "@/lib/utils";
import type { MemoryScope } from "@/lib/types";

const scopes: MemoryScope[] = ["session", "task", "project", "decision", "agent_run"];

function MatchScore({ score }: { score: number }) {
  const pct = Math.round(Math.min(1, Math.max(0, score)) * 100);
  return (
    <div className="mt-1 flex items-center gap-2" title={`Relevance score ${score.toFixed(3)}`}>
      <div className="h-1.5 w-20 shrink-0 overflow-hidden rounded-full bg-surface">
        <div
          className="h-full rounded-full bg-gradient-to-r from-accent-gold to-accent-gold-soft transition-[width] duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
      <span className="text-xs font-medium text-accent-gold">{pct}% match</span>
    </div>
  );
}

export default function Memory() {
  const t = useT();
  return (
    <div className="space-y-6">
      <PageHeader
        title={t("pages.memory.title")}
        description={t("pages.memory.description")}
      />
      <Tabs defaultValue="search">
        <TabsList>
          <TabsTrigger value="search">
            <SearchIcon className="mr-1.5 inline h-3.5 w-3.5" /> Search
          </TabsTrigger>
          <TabsTrigger value="write">
            <PenLine className="mr-1.5 inline h-3.5 w-3.5" /> Write
          </TabsTrigger>
        </TabsList>
        <TabsContent value="search" className="mt-4">
          <MemorySearchPanel />
        </TabsContent>
        <TabsContent value="write" className="mt-4">
          <MemoryWritePanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function MemorySearchPanel() {
  const t = useT();
  const [query, setQuery] = useState("");
  const [scope, setScope] = useState<MemoryScope | "">("");
  const [projectId, setProjectId] = useState("");
  const [limit, setLimit] = useState(20);
  const [view, setView] = useState<"list" | "graph">("list");
  const [pendingDelete, setPendingDelete] = useState<string | null>(null);
  const { push } = useToast();
  const deleteMemory = useDeleteMemory();

  const results = useMemorySearch({
    query: query || null,
    scopes: scope ? [scope] : [],
    project_id: projectId || null,
    limit,
  });

  const confirmDelete = () => {
    if (!pendingDelete) return;
    deleteMemory.mutate(pendingDelete, {
      onSuccess: () => {
        push({ tone: "success", title: "Memory deleted" });
        setPendingDelete(null);
      },
      onError: (error) => push({ tone: "error", title: "Delete failed", description: (error as Error).message }),
    });
  };

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="grid gap-3 pt-5 sm:grid-cols-4">
          <div className="sm:col-span-2">
            <Label htmlFor="q">Query</Label>
            <Input id="q" value={query} onChange={(e) => setQuery(e.target.value)} placeholder={t("pages.memory.searchHint")} />
          </div>
          <div>
            <Label htmlFor="scope">Scope</Label>
            <Select id="scope" value={scope} onChange={(e) => setScope(e.target.value as MemoryScope | "")}>
              <option value="">{t("common.allScopes")}</option>
              {scopes.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="project">Project ID</Label>
            <Input id="project" value={projectId} onChange={(e) => setProjectId(e.target.value)} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Brain className="h-4 w-4 text-accent-gold" /> Results
          </CardTitle>
          <div className="flex items-center gap-2">
            <Select value={String(limit)} onChange={(e) => setLimit(Number(e.target.value))} className="w-28">
              {[10, 20, 50, 100].map((n) => (
                <option key={n} value={n}>
                  {n} results
                </option>
              ))}
            </Select>
            <div className="glass-ambient flex rounded-lg border border-hairline p-0.5">
              <button
                onClick={() => setView("list")}
                aria-label={t("pages.memory.listView")}
                className={`rounded-md p-1.5 transition-colors ${view === "list" ? "bg-accent-gold/10 text-accent-gold" : "text-content-muted hover:text-content-primary"}`}
              >
                <List className="h-4 w-4" />
              </button>
              <button
                onClick={() => setView("graph")}
                aria-label={t("pages.memory.graphView")}
                className={`rounded-md p-1.5 transition-colors ${view === "graph" ? "bg-accent-gold/10 text-accent-gold" : "text-content-muted hover:text-content-primary"}`}
              >
                <Share2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          {results.isLoading ? (
            <SkeletonRows rows={4} />
          ) : results.isError ? (
            <ErrorState error={results.error} onRetry={() => results.refetch()} />
          ) : !results.data?.length ? (
            <EmptyState icon={<Brain className="h-5 w-5" />} title={t("pages.memory.emptyTitle")} description={t("pages.memory.emptyBody")} />
          ) : view === "graph" ? (
            <MemoryGraph records={results.data} />
          ) : (
            <ul className="divide-y divide-surface">
              <AnimatePresence initial={false}>
                {results.data.map((record, i) => (
                  <motion.li
                    key={record.id}
                    initial={{ opacity: 0, y: 4 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    transition={{ duration: 0.2, delay: Math.min(i, 8) * 0.03 }}
                    className="py-3"
                  >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <p className="truncate text-sm font-medium text-content-primary">{record.key}</p>
                        <Badge tone="gold" className="capitalize">
                          {record.scope}
                        </Badge>
                      </div>
                      {record.score != null && <MatchScore score={record.score} />}
                      <p className="mt-1 text-sm text-content-secondary">{truncate(record.content, 220)}</p>
                      <div className="mt-1.5 flex flex-wrap items-center gap-2 text-xs text-content-muted">
                        <span>Importance {record.importance.toFixed(2)}</span>
                        <span>·</span>
                        <span>{formatDateTime(record.created_at)}</span>
                        {record.tags.map((tag) => (
                          <Badge key={tag} tone="neutral">
                            {tag}
                          </Badge>
                        ))}
                      </div>
                    </div>
                    <Button variant="ghost" size="icon" onClick={() => setPendingDelete(record.id)} aria-label={t("pages.memory.deleteMemory")}>
                      <Trash2 className="h-4 w-4 text-accent-red" />
                    </Button>
                  </div>
                  </motion.li>
                ))}
              </AnimatePresence>
            </ul>
          )}
        </CardContent>
      </Card>

      <ConfirmDialog
        open={Boolean(pendingDelete)}
        onClose={() => setPendingDelete(null)}
        onConfirm={confirmDelete}
        title={t("pages.memory.deleteTitle")}
        description={t("pages.memory.deleteBody")}
        confirmLabel="Delete"
        danger
        loading={deleteMemory.isPending}
      />
    </div>
  );
}

function MemoryWritePanel() {
  const [scope, setScope] = useState<MemoryScope>("project");
  const [key, setKey] = useState("");
  const [content, setContent] = useState("");
  const [tags, setTags] = useState("");
  const [importance, setImportance] = useState(0.5);
  const writeMemory = useWriteMemory();
  const { push } = useToast();

  const submit = () => {
    if (!key.trim() || !content.trim()) {
      push({ tone: "error", title: "Key and content are required" });
      return;
    }
    writeMemory.mutate(
      {
        scope,
        key,
        content,
        tags: tags.split(",").map((t) => t.trim()).filter(Boolean),
        importance,
      },
      {
        onSuccess: () => {
          push({ tone: "success", title: "Memory written" });
          setKey("");
          setContent("");
          setTags("");
        },
        onError: (error) => push({ tone: "error", title: "Write failed", description: (error as Error).message }),
      }
    );
  };

  return (
    <Card>
      <CardContent className="space-y-4 pt-5">
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <Label htmlFor="w-scope">Scope</Label>
            <Select id="w-scope" value={scope} onChange={(e) => setScope(e.target.value as MemoryScope)}>
              {scopes.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </Select>
          </div>
          <div>
            <Label htmlFor="w-key">Key</Label>
            <Input id="w-key" value={key} onChange={(e) => setKey(e.target.value)} placeholder="architecture-decision" />
          </div>
        </div>
        <div>
          <Label htmlFor="w-content">Content</Label>
          <Textarea id="w-content" value={content} onChange={(e) => setContent(e.target.value)} rows={4} />
        </div>
        <div className="grid gap-3 sm:grid-cols-2">
          <div>
            <Label htmlFor="w-tags">Tags (comma separated)</Label>
            <Input id="w-tags" value={tags} onChange={(e) => setTags(e.target.value)} placeholder="db, decision" />
          </div>
          <div>
            <Label htmlFor="w-importance">Importance ({importance.toFixed(2)})</Label>
            <input
              id="w-importance"
              type="range"
              min={0}
              max={1}
              step={0.05}
              value={importance}
              onChange={(e) => setImportance(Number(e.target.value))}
              className="mt-2.5 w-full accent-gold-500"
            />
          </div>
        </div>
        <Button onClick={submit} loading={writeMemory.isPending}>
          Write memory
        </Button>
      </CardContent>
    </Card>
  );
}
