import { useState } from "react";
import { motion } from "framer-motion";
import { Bot, PlayCircle, CheckCircle2, XCircle, Zap } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Textarea, Input, Label } from "@/components/ui/Input";
import { Badge } from "@/components/ui/Badge";
import { ErrorState, LoadingState, EmptyState } from "@/components/ui/States";
import { JSONViewer } from "@/components/ui/JSONViewer";
import { AgentCard } from "@/components/agents/AgentCard";
import { Timeline, type TimelineStep } from "@/components/ui/Timeline";
import { useAutonomousRun, useHealth } from "@/lib/api/queries";
import { useToast } from "@/components/ui/Toast";

export default function Autonomous() {
  const [objective, setObjective] = useState("");
  const [context, setContext] = useState("");
  const [projectId, setProjectId] = useState("");
  const run = useAutonomousRun();
  const health = useHealth();
  const { push } = useToast();

  const submit = () => {
    if (objective.trim().length < 3) {
      push({ tone: "error", title: "Objective is too short" });
      return;
    }
    run.mutate({ objective, context: context || null, project_id: projectId || null });
  };

  const result = run.data;
  const steps: TimelineStep[] = result
    ? [
        { id: "plan", title: "Planner", status: "complete", description: `${result.plan.jobs.length} specialist jobs generated` },
        {
          id: "specialists",
          title: "Specialist execution",
          status: result.results.every((r) => !r.error) ? "complete" : "error",
          description: `${result.results.filter((r) => !r.error).length}/${result.results.length} succeeded`,
        },
        {
          id: "verify",
          title: "Verifier",
          status: result.verification.approved ? "complete" : "error",
          description: result.verification.feedback,
        },
        { id: "synthesis", title: "Final synthesis", status: "complete" },
      ]
    : [];

  return (
    <div className="space-y-6">
      <PageHeader
        title="Autonomous Runs"
        description="Planner → specialist jobs → verifier → synthesis, fully autonomous from a single objective."
      />

      <Card>
        <CardContent className="space-y-4 pt-5">
          <div>
            <Label htmlFor="objective">Objective</Label>
            <Textarea id="objective" value={objective} onChange={(e) => setObjective(e.target.value)} rows={2} />
          </div>
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <Label htmlFor="context">Context (optional)</Label>
              <Textarea id="context" value={context} onChange={(e) => setContext(e.target.value)} rows={2} />
            </div>
            <div>
              <Label htmlFor="project">Project ID (optional)</Label>
              <Input id="project" value={projectId} onChange={(e) => setProjectId(e.target.value)} />
            </div>
          </div>
          <Button onClick={submit} loading={run.isPending}>
            <PlayCircle className="h-4 w-4" /> Run autonomously
          </Button>
        </CardContent>
      </Card>

      {run.isPending && (
        <Card>
          <CardContent className="pt-5">
            <LoadingState label="Planning, executing specialists, and verifying…" />
          </CardContent>
        </Card>
      )}

      {run.isError && (
        <Card>
          <CardContent className="pt-5">
            <ErrorState error={run.error} onRetry={submit} />
          </CardContent>
        </Card>
      )}

      {result && (
        <div className="grid gap-4 lg:grid-cols-3">
          <Card className="lg:col-span-1">
            <CardHeader>
              <CardTitle>Execution stages</CardTitle>
            </CardHeader>
            <CardContent>
              <Timeline steps={steps} />
            </CardContent>
          </Card>

          <div className="space-y-4 lg:col-span-2">
            <Card>
              <CardHeader className="flex-col items-stretch gap-2 sm:flex-row sm:items-center">
                <CardTitle className="flex items-center gap-2">
                  <Bot className="h-4 w-4 text-accent-gold" /> Specialist jobs
                </CardTitle>
                <div className="flex flex-wrap items-center gap-2 sm:ml-auto">
                  {health.data && (
                    <Badge tone="gold">
                      <Zap className="h-3 w-3" /> Up to {health.data.max_parallel} in parallel
                    </Badge>
                  )}
                  <Badge tone={result.verification.approved ? "green" : "red"}>
                    {result.verification.approved ? <CheckCircle2 className="h-3 w-3" /> : <XCircle className="h-3 w-3" />}
                    {result.verification.approved ? "Approved" : "Not approved"}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="grid gap-2 sm:grid-cols-2">
                {result.plan.jobs.map((job, i) => {
                  const r = result.results.find((res) => res.name === job.name);
                  return (
                    <motion.div
                      key={job.name}
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: Math.min(i, 8) * 0.05, duration: 0.25 }}
                    >
                      <AgentCard
                        name={job.name}
                        instruction={job.task}
                        status={r ? (r.error ? "failed" : "success") : "pending"}
                        output={r?.output}
                        error={r?.error}
                        attempts={r?.attempts}
                      />
                    </motion.div>
                  );
                })}
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Final answer</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <p className="whitespace-pre-wrap text-sm text-content-primary">{result.final_answer}</p>
                <JSONViewer data={result} />
              </CardContent>
            </Card>
          </div>
        </div>
      )}

      {!result && !run.isPending && !run.isError && (
        <EmptyState
          icon={<Bot className="h-5 w-5" />}
          title="No autonomous run yet"
          description="Submit an objective above to watch the planner, specialists, and verifier work."
        />
      )}
    </div>
  );
}
