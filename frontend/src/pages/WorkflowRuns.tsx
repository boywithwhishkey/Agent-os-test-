import { useState } from "react";
import { History, Search, PlayCircle } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label } from "@/components/ui/Input";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { SkeletonRows } from "@/components/ui/Skeleton";
import { JSONViewer } from "@/components/ui/JSONViewer";
import { useWorkflowRun, useResumeWorkflow } from "@/lib/api/queries";
import { useSessionHistory } from "@/lib/session-history";
import { useToast } from "@/components/ui/Toast";

export default function WorkflowRuns() {
  const history = useSessionHistory("workflow-run");
  const [lookupId, setLookupId] = useState("");
  const [activeId, setActiveId] = useState<string | undefined>();

  return (
    <div className="space-y-6">
      <PageHeader
        title="Workflow Runs"
        description="Inspect a run by ID and resume it past approval pauses. The API does not expose a run list, so this session's runs are tracked below."
      />

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-4 w-4 text-accent-gold" /> Look up a run
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="flex gap-2">
            <Input
              value={lookupId}
              onChange={(e) => setLookupId(e.target.value)}
              placeholder="Paste a workflow run ID"
              onKeyDown={(e) => e.key === "Enter" && setActiveId(lookupId)}
            />
            {/* shrink-0 + nowrap: at 320px the flex row squeezed this button
                until "Look up" wrapped onto two lines mid-phrase. */}
            <Button
              variant="secondary"
              className="shrink-0 whitespace-nowrap"
              onClick={() => setActiveId(lookupId)}
            >
              Look up
            </Button>
          </div>
          <RunDetail runId={activeId} />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <History className="h-4 w-4 text-accent-gold" /> This session's runs
          </CardTitle>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <EmptyState title="No workflow runs yet" description="Runs started from the Workflows editor appear here." />
          ) : (
            <ul className="divide-y divide-surface">
              {history.map((entry) => (
                <li key={entry.id} className="flex items-center justify-between gap-3 py-2.5">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-content-primary">{entry.label}</p>
                    <p className="font-mono text-xs text-content-muted">{entry.id}</p>
                  </div>
                  <Button size="sm" variant="ghost" onClick={() => setActiveId(entry.id)}>
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

function RunDetail({ runId }: { runId: string | undefined }) {
  const { data, isLoading, isError, error, refetch } = useWorkflowRun(runId);
  const resume = useResumeWorkflow();
  const { push } = useToast();
  const [approvalInputs, setApprovalInputs] = useState<Record<string, string>>({});

  if (!runId) return <p className="text-sm text-content-muted">Enter a run ID to inspect its steps.</p>;
  if (isLoading) return <SkeletonRows rows={4} />;
  if (isError) return <ErrorState error={error} onRetry={() => refetch()} />;
  if (!data) return null;

  const steps = Object.values(data.steps);
  const waiting = steps.filter((s) => s.status === "waiting_approval");

  const submitResume = () => {
    const approvals = Object.fromEntries(Object.entries(approvalInputs).filter(([, v]) => v.trim()));
    if (Object.keys(approvals).length === 0) {
      push({ tone: "error", title: "Provide at least one approval ID" });
      return;
    }
    resume.mutate(
      { runId: data.id, approvals },
      {
        onSuccess: () => {
          push({ tone: "success", title: "Workflow resumed" });
          refetch();
        },
        onError: (err) => push({ tone: "error", title: "Resume failed", description: (err as Error).message }),
      }
    );
  };

  return (
    <div className="glass-ambient space-y-4 rounded-lg border border-hairline p-4">
      <div className="flex items-center justify-between">
        <StatusBadge status={data.status} />
        <span className="font-mono text-xs text-content-muted">{data.id}</span>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full min-w-[480px] text-sm">
          <thead>
            <tr className="border-b border-hairline text-left text-xs uppercase tracking-wider text-content-muted">
              <th className="py-2 pr-3 font-medium">Step</th>
              <th className="py-2 pr-3 font-medium">Status</th>
              <th className="py-2 pr-3 font-medium">Attempts</th>
              <th className="py-2 font-medium">Error</th>
            </tr>
          </thead>
          <tbody>
            {steps.map((step) => (
              <tr key={step.step_id} className="border-b border-hairline last:border-0">
                <td className="py-2 pr-3 font-medium text-content-primary">{step.step_id}</td>
                <td className="py-2 pr-3">
                  <StatusBadge status={step.status} />
                </td>
                <td className="py-2 pr-3 text-content-muted">{step.attempts}</td>
                <td className="py-2 text-accent-red">{step.error ?? "—"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {waiting.length > 0 && (
        <div className="space-y-3 rounded-lg border border-accent-amber/25 bg-accent-amber/5 p-3">
          <p className="text-sm font-medium text-content-primary">Resume paused steps</p>
          {waiting.map((step) => (
            <div key={step.step_id} className="flex flex-col gap-1 sm:flex-row sm:items-center sm:gap-2">
              <Label className="mb-0 sm:w-32 sm:shrink-0">{step.step_id}</Label>
              <Input
                placeholder="Approval ID"
                value={approvalInputs[step.step_id] ?? ""}
                onChange={(e) => setApprovalInputs((prev) => ({ ...prev, [step.step_id]: e.target.value }))}
              />
            </div>
          ))}
          <Button size="sm" onClick={submitResume} loading={resume.isPending}>
            <PlayCircle className="h-3.5 w-3.5" /> Resume workflow
          </Button>
        </div>
      )}

      <JSONViewer data={data} />
    </div>
  );
}
