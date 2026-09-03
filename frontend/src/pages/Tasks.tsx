import { useState } from "react";
import { useT } from "@/lib/i18n";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Plus, Search, ListTodo } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label, Select, FieldError } from "@/components/ui/Input";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Badge } from "@/components/ui/Badge";
import { EmptyState, ErrorState } from "@/components/ui/States";
import { SkeletonRows } from "@/components/ui/Skeleton";
import { useCreateTask, useTask } from "@/lib/api/queries";
import { useSessionHistory, recordHistory } from "@/lib/session-history";
import { useToast } from "@/components/ui/Toast";
import { formatDateTime, truncate } from "@/lib/utils";

const schema = z.object({
  objective: z.string().min(3, "Objective must be at least 3 characters").max(2000),
  priority: z.enum(["low", "normal", "high", "critical"]),
  project_id: z.string().optional(),
});
type FormValues = z.infer<typeof schema>;

export default function Tasks() {
  const t = useT();
  const { push } = useToast();
  const createTask = useCreateTask();
  const history = useSessionHistory("task");
  const [lookupId, setLookupId] = useState("");
  const [activeLookup, setActiveLookup] = useState<string | undefined>();

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: { priority: "normal" },
  });

  const onSubmit = handleSubmit((values) => {
    createTask.mutate(
      {
        objective: values.objective,
        priority: values.priority,
        project_id: values.project_id || null,
      },
      {
        onSuccess: (task) => {
          recordHistory("task", {
            id: task.id,
            label: truncate(task.objective, 60),
            createdAt: task.created_at,
          });
          setActiveLookup(task.id);
          push({ tone: "success", title: "Task created", description: task.id });
          reset({ objective: "", priority: "normal", project_id: "" });
        },
        onError: (error) => {
          push({ tone: "error", title: "Could not create task", description: (error as Error).message });
        },
      }
    );
  });

  return (
    <div className="space-y-6">
      <PageHeader
        title={t("pages.tasks.title")}
        description={t("pages.tasks.description")}
      />

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Plus className="h-4 w-4 text-accent-gold" /> New task
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={onSubmit} className="space-y-4">
              <div>
                <Label htmlFor="objective">Objective</Label>
                <Input id="objective" {...register("objective")} placeholder="Build the onboarding flow" />
                <FieldError>{errors.objective?.message}</FieldError>
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
                <div>
                  <Label htmlFor="priority">Priority</Label>
                  <Select id="priority" {...register("priority")}>
                    <option value="low">{t("common.priorityLow")}</option>
                    <option value="normal">{t("common.priorityNormal")}</option>
                    <option value="high">{t("common.priorityHigh")}</option>
                    <option value="critical">{t("common.priorityCritical")}</option>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="project_id">Project ID (optional)</Label>
                  <Input id="project_id" {...register("project_id")} placeholder="agent-os" />
                </div>
              </div>
              <Button type="submit" loading={createTask.isPending} className="w-full sm:w-auto">
                Create task
              </Button>
            </form>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Search className="h-4 w-4 text-accent-gold" /> Look up a task
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex gap-2">
              <Input
                value={lookupId}
                onChange={(e) => setLookupId(e.target.value)}
                placeholder={t("pages.tasks.lookupPlaceholder")}
                onKeyDown={(e) => e.key === "Enter" && setActiveLookup(lookupId)}
              />
              <Button variant="secondary" onClick={() => setActiveLookup(lookupId)}>
                Look up
              </Button>
            </div>
            <TaskLookupResult taskId={activeLookup} />
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>{t("common.sessionTasks")}</CardTitle>
        </CardHeader>
        <CardContent>
          {history.length === 0 ? (
            <EmptyState
              icon={<ListTodo className="h-5 w-5" />}
              title={t("pages.tasks.emptyTitle")}
              description={t("pages.tasks.emptyBody")}
            />
          ) : (
            <ul className="divide-y divide-surface">
              {history.map((entry) => (
                <li key={entry.id} className="flex items-center justify-between gap-3 py-2.5">
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium text-content-primary">{entry.label}</p>
                    <p className="font-mono text-xs text-content-muted">{entry.id}</p>
                  </div>
                  <Button size="sm" variant="ghost" onClick={() => setActiveLookup(entry.id)}>
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

function TaskLookupResult({ taskId }: { taskId: string | undefined }) {
  const { data, isLoading, isError, error, refetch } = useTask(taskId);

  if (!taskId) {
    return <p className="text-sm text-content-muted">Enter a task ID to inspect its status.</p>;
  }
  if (isLoading) return <SkeletonRows rows={3} />;
  if (isError) return <ErrorState error={error} onRetry={() => refetch()} />;
  if (!data) return null;

  return (
    <div className="space-y-2 glass-ambient rounded-lg border border-hairline p-4">
      <div className="flex items-center justify-between">
        <StatusBadge status={data.status} />
        <Badge tone="gold" className="capitalize">
          {data.priority}
        </Badge>
      </div>
      <p className="text-sm text-content-primary">{data.objective}</p>
      <dl className="grid grid-cols-1 gap-2 text-xs text-content-muted sm:grid-cols-2">
        <div>
          <dt className="font-medium">Project</dt>
          <dd>{data.project_id ?? "—"}</dd>
        </div>
        <div>
          <dt className="font-medium">Created</dt>
          <dd>{formatDateTime(data.created_at)}</dd>
        </div>
      </dl>
    </div>
  );
}
