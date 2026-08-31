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
import { PulseEdge } from "@/components/workflows/PulseEdge";
import { useRunWorkflow } from "@/lib/api/queries";
import { useToast } from "@/components/ui/Toast";
import { useTheme } from "@/lib/theme";
import { recordHistory } from "@/lib/session-history";
import { validateWorkflowGraph, invalidStepIds } from "@/lib/workflow-validate";
import type { WorkflowStep } from "@/lib/types";
import { Link } from "react-router-dom";

const nodeTypes = { step: StepNode };
const edgeTypes = { pulse: PulseEdge };

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
  const { resolvedTheme } = useTheme();
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
      setEdges((eds) => addEdge({ ...connection, animated: true, style: { stroke: "var(--color-accent-gold)" } }, eds));
    },
    [setEdges]
  );

  const editStep = useCallback(
    (nodeId: string) => {
      const step = stepsFromGraph().find((s) => s.id === nodeId);
      if (step) {
        setEditingStep(step);
        setDialogOpen(true);
      }
    },
    [stepsFromGraph]
  );

  const deleteStep = useCallback(
    (nodeId: string) => {
      setNodes((nds) => nds.filter((n) => n.id !== nodeId));
      setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId));
    },
    [setNodes, setEdges]
  );

  const onNodeClick: NodeMouseHandler<Node<StepNodeData>> = (_, node) => editStep(node.id);

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

  const invalidIds = useMemo(() => invalidStepIds(validationErrors), [validationErrors]);

  const displayNodes = useMemo(
    () =>
      nodes.map((n) => ({
        ...n,
        data: {
          ...n.data,
          hasValidationError: invalidIds.has(n.id),
          onEdit: () => editStep(n.id),
          onDelete: () => deleteStep(n.id),
        },
      })),
    [nodes, invalidIds, editStep, deleteStep]
  );

  const displayEdges = useMemo(() => {
    const statusById = new Map(nodes.map((n) => [n.id, n.data.runStatus]));
    return edges.map((e) => ({
      ...e,
      type: "pulse",
      data: {
        active: statusById.get(e.source) === "running" || statusById.get(e.target) === "running",
      },
    }));
  }, [edges, nodes]);

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
            <GitBranch className="h-4 w-4 text-accent-gold" /> Step graph
          </CardTitle>
          <div className="flex flex-wrap gap-2">
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
              nodes={displayNodes}
              edges={displayEdges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              nodeTypes={nodeTypes}
              edgeTypes={edgeTypes}
              defaultEdgeOptions={{
                animated: true,
                style: { stroke: "var(--color-accent-gold)", strokeWidth: 2 },
              }}
              fitView
              // Without a maxZoom, fitView scales to React Flow's default
              // maxZoom of 2 whenever the graph is small — a brand-new
              // workflow has one node, so the canvas opened at 200% and the
              // single "start" node rendered comically oversized at every
              // viewport. Cap the auto-fit at 100%; the user can still zoom.
              fitViewOptions={{ maxZoom: 1, padding: 0.25 }}
              deleteKeyCode={["Backspace", "Delete"]}
              // React Flow's own chrome (Controls, MiniMap) ships light-mode
              // styling by default, which rendered as stark white blocks on
              // the dark UI. colorMode themes them from the app's theme.
              colorMode={resolvedTheme}
            >
              <Background gap={18} />
              <Controls />
              <MiniMap pannable zoomable />
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
