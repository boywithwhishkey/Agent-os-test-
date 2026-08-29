import { Handle, Position, NodeToolbar, type NodeProps } from "@xyflow/react";
import { Cog, Wrench, Bot, Plug, CircleDashed, CheckCircle2, XCircle, Loader2, ShieldAlert, AlertTriangle, Pencil, Trash2 } from "lucide-react";
import { cn } from "@/lib/utils";
import type { StepStatus, StepType } from "@/lib/types";

export interface StepNodeData extends Record<string, unknown> {
  stepId: string;
  type: StepType;
  maxRetries: number;
  timeoutSeconds: number;
  runStatus?: StepStatus;
  hasValidationError?: boolean;
  onEdit?: () => void;
  onDelete?: () => void;
}

const typeIcons: Record<StepType, typeof Cog> = {
  noop: CircleDashed,
  tool: Wrench,
  agent: Bot,
  integration: Plug,
};

const statusStyles: Record<
  StepStatus,
  { border: string; icon: typeof CheckCircle2 | null; className: string; glow?: string }
> = {
  pending: { border: "border-hairline", icon: null, className: "" },
  running: {
    border: "border-accent-blue",
    icon: Loader2,
    className: "text-accent-blue animate-spin",
    glow: "shadow-[0_0_18px_-3px_var(--color-accent-blue)] animate-pulse-slow",
  },
  completed: { border: "border-accent-green", icon: CheckCircle2, className: "text-accent-green" },
  failed: { border: "border-accent-red", icon: XCircle, className: "text-accent-red" },
  skipped: { border: "border-hairline", icon: null, className: "text-content-muted" },
  waiting_approval: {
    border: "border-accent-amber",
    icon: ShieldAlert,
    className: "text-accent-amber",
    glow: "shadow-[0_0_18px_-3px_var(--color-accent-amber)] animate-breathe",
  },
};

export function StepNode({ data, selected }: NodeProps & { data: StepNodeData }) {
  const Icon = typeIcons[data.type] ?? Cog;
  const status = data.runStatus;
  const statusStyle = status ? statusStyles[status] : null;
  const StatusIcon = statusStyle?.icon ?? null;
  const invalid = Boolean(data.hasValidationError);

  return (
    <div
      className={cn(
        "glass-soft min-w-[180px] rounded-lg border-2 px-3 py-2.5 transition-colors",
        invalid ? "border-accent-red border-dashed" : statusStyle?.border ?? "border-hairline",
        !invalid && statusStyle?.glow,
        selected && "ring-2 ring-accent-violet/50"
      )}
    >
      <NodeToolbar isVisible={selected} position={Position.Top} className="glass-focus flex gap-1 rounded-lg border border-hairline p-1">
        <button
          onClick={data.onEdit}
          className="focus-ring flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-content-secondary hover:bg-surface-hover hover:text-content-primary"
        >
          <Pencil className="h-3 w-3" /> Edit
        </button>
        <button
          onClick={data.onDelete}
          className="focus-ring flex items-center gap-1 rounded-md px-2 py-1 text-xs font-medium text-accent-red hover:bg-accent-red/10"
        >
          <Trash2 className="h-3 w-3" /> Delete
        </button>
      </NodeToolbar>
      <Handle type="target" position={Position.Top} className="!bg-accent-violet" />
      <div className="flex items-center gap-2">
        <span className="flex h-6 w-6 items-center justify-center rounded-md bg-accent-violet/10 text-accent-violet">
          <Icon className="h-3.5 w-3.5" />
        </span>
        <span className="truncate text-sm font-medium text-content-primary">{data.stepId}</span>
        {invalid ? (
          <AlertTriangle className="ml-auto h-3.5 w-3.5 text-accent-red" aria-label="Validation error" />
        ) : (
          StatusIcon && <StatusIcon className={cn("ml-auto h-3.5 w-3.5", statusStyle?.className)} />
        )}
      </div>
      <p className="mt-1 text-xs capitalize text-content-muted">
        {data.type} · retries {data.maxRetries} · {data.timeoutSeconds}s
      </p>
      <Handle type="source" position={Position.Bottom} className="!bg-accent-violet" />
    </div>
  );
}
