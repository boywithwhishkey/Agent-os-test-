import { useState } from "react";
import { PlayCircle, CheckCircle2, XCircle, Copy, Sparkles } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Textarea, Label } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { ErrorState, LoadingState, EmptyState } from "@/components/ui/States";
import { JSONViewer } from "@/components/ui/JSONViewer";
import { AgentCard } from "@/components/agents/AgentCard";
import { OrchestrationPipeline } from "@/components/agents/OrchestrationPipeline";
import type { AgentCardStatus } from "@/components/agents/AgentCard";
import { useOrchestrate } from "@/lib/api/queries";
import { useToast } from "@/components/ui/Toast";

export default function Orchestrate() {
  const [objective, setObjective] = useState("");
  const [context, setContext] = useState("");
  const orchestrate = useOrchestrate();
  const { push } = useToast();

  const run = () => {
    if (objective.trim().length < 3) {
      push({ tone: "error", title: "Objective is too short", description: "Enter at least 3 characters." });
      return;
    }
    orchestrate.mutate({ objective, context: context || null });
  };

  const result = orchestrate.data;
  const combined = result
    ? result.plan.jobs.map((job) => ({
        job,
        result: result.results.find((r) => r.job_id === job.id),
      }))
    : [];
  const pipelineStatuses: Record<string, AgentCardStatus> = Object.fromEntries(
    combined.map(({ job, result: r }) => [job.role, r ? (r.success ? "success" : "failed") : "pending"])
  );

  return (
    <div className="space-y-6">
      <PageHeader
        title="Orchestrate"
        description="Run a researcher → builder → reviewer multi-agent orchestration against a single objective."
      />

      <Card>
        <CardContent className="space-y-4 pt-5">
          <div>
            <Label htmlFor="objective">Objective</Label>
            <Textarea
              id="objective"
              value={objective}
              onChange={(e) => setObjective(e.target.value)}
              placeholder="Design a rollout plan for the new billing system"
              rows={2}
            />
          </div>
          <div>
            <Label htmlFor="context">Context (optional)</Label>
            <Textarea
              id="context"
              value={context}
              onChange={(e) => setContext(e.target.value)}
              placeholder="Relevant constraints, prior decisions, or background"
              rows={3}
            />
          </div>
          <Button onClick={run} loading={orchestrate.isPending}>
            <PlayCircle className="h-4 w-4" /> Run orchestration
          </Button>
        </CardContent>
      </Card>

      {orchestrate.isPending && (
        <Card>
          <CardContent className="pt-5">
            <LoadingState label="Researcher, builder, and reviewer are working…" />
          </CardContent>
        </Card>
      )}

      {orchestrate.isError && (
        <Card>
          <CardContent className="pt-5">
            <ErrorState error={orchestrate.error} onRetry={run} />
          </CardContent>
        </Card>
      )}

      {result && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-accent-violet" /> Agent activity
              </CardTitle>
              <Badge tone={result.verification.passed ? "green" : "red"}>
                {result.verification.passed ? (
                  <CheckCircle2 className="h-3 w-3" />
                ) : (
                  <XCircle className="h-3 w-3" />
                )}
                {result.verification.passed ? "Verified" : "Verification failed"}
              </Badge>
            </CardHeader>
            <CardContent className="space-y-3">
              <OrchestrationPipeline statuses={pipelineStatuses} />
              {combined.map(({ job, result: r }) => (
                <AgentCard
                  key={job.id}
                  name={job.role}
                  role={job.role}
                  instruction={job.instruction}
                  status={r ? (r.success ? "success" : "failed") : "pending"}
                  output={r?.output}
                />
              ))}
            </CardContent>
          </Card>

          {result.verification.issues.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Reviewer issues</CardTitle>
              </CardHeader>
              <CardContent>
                <ul className="list-inside list-disc space-y-1 text-sm text-content-secondary">
                  {result.verification.issues.map((issue, i) => (
                    <li key={i}>{issue}</li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          )}

          <Card>
            <CardHeader>
              <CardTitle>Final synthesis</CardTitle>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => navigator.clipboard.writeText(result.results.map((r) => r.output).join("\n\n"))}
              >
                <Copy className="h-3.5 w-3.5" /> Copy outputs
              </Button>
            </CardHeader>
            <CardContent className="space-y-3">
              <p className="text-sm text-content-secondary">Objective: {result.objective}</p>
              <JSONViewer data={result} />
            </CardContent>
          </Card>
        </div>
      )}

      {!result && !orchestrate.isPending && !orchestrate.isError && (
        <EmptyState
          icon={<Sparkles className="h-5 w-5" />}
          title="No orchestration run yet"
          description="Enter an objective above and run it to see researcher, builder, and reviewer activity."
        />
      )}
    </div>
  );
}
