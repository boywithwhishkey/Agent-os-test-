import { useState } from "react";
import { ChevronDown, ChevronRight, Search, Hammer, Eye, Bot as BotIcon, CheckCircle2, XCircle, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import { cn } from "@/lib/utils";
import type { AgentRole } from "@/lib/types";

export type AgentCardStatus = "pending" | "running" | "success" | "failed";

const roleIcons: Record<string, typeof Search> = {
  researcher: Search,
  builder: Hammer,
  reviewer: Eye,
};

const statusConfig: Record<AgentCardStatus, { icon: typeof CheckCircle2; className: string; label: string }> = {
  pending: { icon: Loader2, className: "text-content-muted", label: "Pending" },
  running: { icon: Loader2, className: "text-accent-gold-soft animate-spin", label: "Running" },
  success: { icon: CheckCircle2, className: "text-accent-green", label: "Success" },
  failed: { icon: XCircle, className: "text-accent-red", label: "Failed" },
};

export function AgentCard({
  name,
  role,
  instruction,
  status,
  output,
  error,
  attempts,
}: {
  name: string;
  role?: AgentRole | string;
  instruction: string;
  status: AgentCardStatus;
  output?: string | null;
  error?: string | null;
  attempts?: number;
}) {
  const [open, setOpen] = useState(false);
  const RoleIcon = (role && roleIcons[role]) || BotIcon;
  const StatusIcon = statusConfig[status].icon;

  return (
    <motion.div
      layout
      className="glass-soft overflow-hidden rounded-xl border border-hairline"
    >
      <button
        onClick={() => setOpen((o) => !o)}
        className="focus-ring flex w-full items-center gap-3 px-4 py-3 text-left"
      >
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-accent-gold/10 text-accent-gold">
          <RoleIcon className="h-4 w-4" />
        </span>
        <span className="min-w-0 flex-1">
          <span className="flex items-center gap-2">
            <span className="truncate text-sm font-medium text-content-primary capitalize">{name}</span>
            {typeof attempts === "number" && attempts > 1 && (
              <span className="text-xs text-content-muted">· {attempts} attempts</span>
            )}
          </span>
          <span className="mt-0.5 block truncate text-xs text-content-muted">{instruction}</span>
        </span>
        <StatusIcon className={cn("h-4 w-4 shrink-0", statusConfig[status].className)} aria-label={statusConfig[status].label} />
        {open ? <ChevronDown className="h-4 w-4 text-content-muted" /> : <ChevronRight className="h-4 w-4 text-content-muted" />}
      </button>
      {open && (
        <div className="border-t border-hairline px-4 py-3">
          {error ? (
            <p className="text-sm text-accent-red">{error}</p>
          ) : (
            <p className="whitespace-pre-wrap text-sm text-content-secondary">{output || "No output."}</p>
          )}
        </div>
      )}
    </motion.div>
  );
}
