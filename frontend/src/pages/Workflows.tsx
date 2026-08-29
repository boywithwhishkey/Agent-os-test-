import { useCallback, useMemo, useState } from "react";
import {
  ReactFlow,
  ReactFlowProvider,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useNodesState,
  useEdgesState,
  type Connection,
  type Edge,
  type Node,
  type NodeMouseHandler,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Plus, PlayCircle, GitBranch, AlertTriangle } from "lucide-react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Input, Label, Textarea } from "@/components/ui/Input";
import { ErrorState } from "@/components/ui/States";
import { StepNode, type StepNodeData } from "@/components/workflows/StepNode";
import { StepEditorDialog } from "@/components/workflows/StepEditorDialog";
import { useRunWorkflow } from "@/lib/api/queries";
import { useToast } from "@/components/ui/Toast";
import { recordHistory } from "@/lib/session-history";
import { validateWorkflowGraph } from "@/lib/workflow-validate";
import type { WorkflowStep } from "@/lib/types";
import { Link } from "react-router-dom";

const nodeTypes = { step: StepNode };

function stepToNode(step: WorkflowStep, position: { x: number; y: number }): Node<StepNodeData> {
  return {
    id: step.id,
    type: "step",
    position,
    data: { stepId: step.id, type: step.type, maxRetries: step.max_retries, timeoutSeconds: step.timeout_seconds },
  };
}

export default function Workflows() {
  return (
    <ReactFlowProvider>
      <WorkflowEditor />
    </ReactFlowProvider>
  );
}

function WorkflowEditor() {
  const [name, setName] = useState("New workflow");
  const [contextText, setContextText] = useState("{}");
  const [nodes, setNodes, onNodesChange] = useNodesState<Node<StepNodeData>>([
    stepToNode({ id: "start", type: "noop", depends_on: [], input: {}, max_retries: 0, timeout_seconds: 30 }, { x: 250, y: 40 }),
  ]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingStep, setEditingStep] = useState<WorkflowStep | undefined>();
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const runWorkflow = useRunWorkflow();
  const { push } = useToast();

  const stepsFromGraph = useCallback((): WorkflowStep[] => {
    return nodes.map((node) => {
      const dependsOn = edges.filter((e) => e.target === node.id).map((e) => e.source);
      const existing = node.data;
      return {
        id: node.id,
        type: existing.type,
        depends_on: dependsOn,
        input: {},
        condition_key: null,
        condition_equals: undefined,
        max_retries: existing.maxRetries,
        timeout_seconds: existing.timeoutSeconds,
      };
    });
  }, [nodes, edges]);

  const onConnect = useCallback(
    (connection: Connection) => {
      if (connection.source === connection.target) return;
      setEdges((eds) => addEdge({ ...connection, animated: true, style: { stroke: "var(--color-accent-violet)" } }, eds));
    },
    [setEdges]
  );

  const onNodeClick: NodeMouseHandler<Node<StepNodeData>> = (_, node) => {
    const steps = stepsFromGraph();
    const step = steps.find((s) => s.id === node.id);
    if (step) {
      setEditingStep(step);
      setDialogOpen(true);
    }
  };

  const addStep = () => {
    setEditingStep(undefined);
    setDialogOpen(true);
  };

  const onSaveStep = (step: WorkflowStep) => {
    if (editingStep) {
      setNodes((nds) =>
        nds.map((n) => (n.id === step.id ? { ...n, data: { ...n.data, type: step.type, maxRetries: step.max_retries, timeoutSeconds: step.timeout_seconds } } : n))
      );
    } else {
      setNodes((nds) => [...nds, stepToNode(step, { x: 100 + nds.length * 40, y: 140 + nds.length * 90 })]);
    }
  };

  const removeSelected = () => {
    setNodes((nds) => nds.filter((n) => !n.selected));
    setEdges((eds) => eds.filter((e) => !e.selected));
  };

  const existingIds = useMemo(() => nodes.map((n) => n.id), [nodes]);

  const run = () => {
    const steps = stepsFromGraph();
    const errors = validateWorkflowGraph(steps);
    setValidationErrors(errors);
    if (errors.length > 0) return;

    let context: Record<string, unknown> = {};
    try {
      context = contextText.trim() ? JSON.parse(contextText) : {};
    } catch {
      setValidationErrors(["Context must be valid JSON."]);
      return;
    }

    const definitionId = crypto.randomUUID();
    runWorkflow.mutate(
      { definition: { id: definitionId, name, steps }, context },
      {
        onSuccess: (workflowRun) => {
          recordHistory("workflow-run", { id: workflowRun.id, label: name, createdAt: new Date().toISOString() });
          push({ tone: "success", title: "Workflow started", description: `Run ${workflowRun.id}` });
          setNodes((nds) =>
            nds.map((n) => ({
              ...n,
              data: { ...n.data, runStatus: workflowRun.steps[n.id]?.status },
            }))
          );
        },
        onError: (error) => push({ tone: "error", title: "Run failed", description: (error as Error).message }),
      }
    );
  };

  return (
    <div className="space-y-4">
      <PageHeader
        title="Workflows"
        description="Design a step graph, then run it. There's no separate save — running a workflow persists its definition."
        actions={
          <Link to="/workflows/runs">
            <Button variant="outline" size="sm">
              View workflow runs
            </Button>
          </Link>
        }
      />

      <Card>
        <CardContent className="grid gap-3 pt-5 sm:grid-cols-3">
          <div className="sm:col-span-1">
            <Label htmlFor="wf-name">Workflow name</Label>
            <Input id="wf-name" value={name} onChange={(e) => setName(e.target.value)} />
          </div>
          <div className="sm:col-span-2">
            <Label htmlFor="wf-context">Run context (JSON)</Label>
            <Textarea id="wf-context" value={contextText} onChange={(e) => setContextText(e.target.value)} rows={1} className="font-mono text-xs" />
          </div>
        </CardContent>
      </Card>

      {validationErrors.length > 0 && (
        <div className="flex items-start gap-2 rounded-lg border border-accent-red/25 bg-accent-red/5 p-3 text-sm text-accent-red">
          <AlertTriangle className="mt-0.5 h-4 w-4 shrink-0" />
          <ul className="list-inside list-disc">
            {validationErrors.map((err) => (
              <li key={err}>{err}</li>
            ))}
          </ul>
        </div>
      )}

      <Card className="overflow-hidden">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <GitBranch className="h-4 w-4 text-accent-violet" /> Step graph
          </CardTitle>
          <div className="flex gap-2">
            <Button variant="secondary" size="sm" onClick={addStep}>
              <Plus className="h-3.5 w-3.5" /> Add step
            </Button>
            <Button variant="outline" size="sm" onClick={removeSelected}>
              Delete selected
            </Button>
            <Button size="sm" onClick={run} loading={runWorkflow.isPending}>
              <PlayCircle className="h-3.5 w-3.5" /> Run workflow
            </Button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="h-[480px] w-full">
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              nodeTypes={nodeTypes}
              defaultEdgeOptions={{
                type: "smoothstep",
                animated: true,
                style: { stroke: "var(--color-accent-violet)", strokeWidth: 2 },
              }}
              fitView
              deleteKeyCode={["Backspace", "Delete"]}
            >
              <Background gap={18} />
              <Controls />
              <MiniMap pannable zoomable className="!bg-surface-raised" />
            </ReactFlow>
          </div>
        </CardContent>
      </Card>

      {runWorkflow.isError && <ErrorState error={runWorkflow.error} onRetry={run} />}

      <StepEditorDialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        onSave={onSaveStep}
        initial={editingStep}
        existingIds={existingIds}
      />
    </div>
  );
}
