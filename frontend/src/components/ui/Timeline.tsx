import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

export interface TimelineStep {
  id: string;
  title: string;
  description?: ReactNode;
  status: "complete" | "active" | "pending" | "error";
  meta?: string;
}

const dotStyles: Record<TimelineStep["status"], string> = {
  complete: "bg-accent-green border-accent-green",
  active: "bg-accent-blue border-accent-blue animate-pulse-slow",
  pending: "bg-transparent border-hairline",
  error: "bg-accent-red border-accent-red",
};

export function Timeline({ steps }: { steps: TimelineStep[] }) {
  return (
    <ol className="relative space-y-6 pl-6">
      <div className="absolute bottom-2 left-[7px] top-2 w-px bg-surface" aria-hidden />
      {steps.map((step) => (
        <li key={step.id} className="relative">
          <span
            className={cn("absolute -left-6 top-0.5 h-3.5 w-3.5 rounded-full border-2", dotStyles[step.status])}
            aria-hidden
          />
          <div className="flex items-center justify-between gap-2">
            <p className="text-sm font-medium text-content-primary">{step.title}</p>
            {step.meta && <span className="text-xs text-content-muted">{step.meta}</span>}
          </div>
          {step.description && <div className="mt-1 text-sm text-content-secondary">{step.description}</div>}
        </li>
      ))}
    </ol>
  );
}
