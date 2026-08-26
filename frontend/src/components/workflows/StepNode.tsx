import { Handle, Position, type NodeProps } from "@xyflow/react";
import { Cog, Wrench, Bot, Plug, CircleDashed, CheckCircle2, XCircle, Loader2, ShieldAlert } from "lucide-react";
import { cn } from "@/lib/utils";
import type { StepStatus, StepType } from "@/lib/types";

export interface StepNodeData extends Record<string, unknown> {
  stepId: string;
  type: StepType;
  maxRetries: number;
  timeoutSeconds: number;
  runStatus?: StepStatus;
}

const typeIcons: Record<StepType, typeof Cog> = {
  noop: CircleDashed,
  tool: Wrench,
  agent: Bot,
  integration: Plug,
};

const statusStyles: Record<StepStatus, { border: string; icon: typeof CheckCircle2 | null; className: string }> = {
  pending: { border: "border-surface", icon: null, className: "" },
  running: { border: "border-accent-blue", icon: Loader2, className: "text-accent-blue animate-spin" },
  completed: { border: "border-accent-green", icon: CheckCircle2, className: "text-accent-green" },
  failed: { border: "border-accent-red", icon: XCircle, className: "text-accent-red" },
  skipped: { border: "border-surface", icon: null, className: "text-content-muted" },
  waiting_approval: { border: "border-accent-amber", icon: ShieldAlert, className: "text-accent-amber" },
};

export function StepNode({ data, selected }: NodeProps & { data: StepNodeData }) {
  const Icon = typeIcons[data.type] ?? Cog;
  const status = data.runStatus;
  const statusStyle = status ? statusStyles[status] : null;
  const StatusIcon = statusStyle?.icon ?? null;

  return (
    <div
      className={cn(
        "min-w-[180px] rounded-lg border-2 bg-surface-raised px-3 py-2.5 shadow-sm transition-colors",
        statusStyle?.border ?? "border-surface",
        selected && "ring-2 ring-accent-violet/50"
      )}
    >
      <Handle type="target" position={Position.Top} className="!bg-accent-violet" />
      <div className="flex items-center gap-2">
        <span className="flex h-6 w-6 items-center justify-center rounded-md bg-accent-violet/10 text-accent-violet">
          <Icon className="h-3.5 w-3.5" />
        </span>
        <span className="truncate text-sm font-medium text-content-primary">{data.stepId}</span>
        {StatusIcon && <StatusIcon className={cn("ml-auto h-3.5 w-3.5", statusStyle?.className)} />}
      </div>
      <p className="mt-1 text-xs capitalize text-content-muted">
        {data.type} · retries {data.maxRetries} · {data.timeoutSeconds}s
      </p>
      <Handle type="source" position={Position.Bottom} className="!bg-accent-violet" />
    </div>
  );
}
