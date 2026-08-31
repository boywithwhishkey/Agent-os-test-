import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { cn, truncate } from "@/lib/utils";
import type { MemoryRecord, MemoryScope } from "@/lib/types";

const MAX_NODES = 40;

const scopeColor: Record<MemoryScope, string> = {
  session: "var(--color-accent-gold-soft)",
  task: "var(--color-accent-green)",
  project: "var(--color-accent-gold)",
  decision: "var(--color-accent-gold)",
  agent_run: "var(--color-accent-amber)",
};

interface GraphEdge {
  a: number;
  b: number;
  reason: string;
}

function buildEdges(records: MemoryRecord[]): GraphEdge[] {
  const edges: GraphEdge[] = [];
  for (let i = 0; i < records.length; i++) {
    for (let j = i + 1; j < records.length; j++) {
      const a = records[i];
      const b = records[j];
      const sharedTags = a.tags.filter((tag) => b.tags.includes(tag));
      if (sharedTags.length > 0) {
        edges.push({ a: i, b: j, reason: `shared tag: ${sharedTags[0]}` });
      } else if (a.project_id && a.project_id === b.project_id) {
        edges.push({ a: i, b: j, reason: `same project: ${a.project_id}` });
      } else if (a.task_id && a.task_id === b.task_id) {
        edges.push({ a: i, b: j, reason: `same task: ${a.task_id}` });
      }
    }
  }
  return edges;
}

/**
 * A relationship graph of the current search results. Edges are drawn only
 * from genuinely shared fields (tags/project/task) — there is no
 * memory-to-memory similarity score available from the API, only
 * query-to-record relevance, so this deliberately doesn't pretend otherwise.
 */
export function MemoryGraph({ records }: { records: MemoryRecord[] }) {
  const [hovered, setHovered] = useState<number | null>(null);
  const size = 480;
  const center = size / 2;
  const radius = size / 2 - 56;

  const shown = useMemo(() => records.slice(0, MAX_NODES), [records]);

  const positions = useMemo(
    () =>
      shown.map((_, i) => {
        const angle = (2 * Math.PI * i) / Math.max(1, shown.length) - Math.PI / 2;
        return { x: center + radius * Math.cos(angle), y: center + radius * Math.sin(angle) };
      }),
    [shown, center, radius]
  );

  const edges = useMemo(() => buildEdges(shown), [shown]);

  if (shown.length === 0) return null;

  return (
    <div className="space-y-2">
      {records.length > MAX_NODES && (
        <p className="text-xs text-content-muted">Showing the first {MAX_NODES} of {records.length} results.</p>
      )}
      <div className="flex justify-center overflow-x-auto">
        <svg width={size} height={size} className="max-w-full">
          <g>
            {edges.map((edge, i) => {
              const active = hovered === edge.a || hovered === edge.b;
              return (
                <line
                  key={i}
                  x1={positions[edge.a].x}
                  y1={positions[edge.a].y}
                  x2={positions[edge.b].x}
                  y2={positions[edge.b].y}
                  stroke={active ? "var(--color-accent-gold)" : "currentColor"}
                  strokeOpacity={active ? 0.8 : 0.15}
                  strokeWidth={active ? 2 : 1}
                  className="text-content-muted transition-all"
                >
                  <title>{edge.reason}</title>
                </line>
              );
            })}
          </g>
          {shown.map((record, i) => {
            const pos = positions[i];
            const isHovered = hovered === i;
            return (
              <motion.g
                key={record.id}
                initial={{ opacity: 0, scale: 0.5 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: Math.min(i, 20) * 0.02, duration: 0.25 }}
                onMouseEnter={() => setHovered(i)}
                onMouseLeave={() => setHovered(null)}
                className="cursor-pointer"
              >
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={isHovered ? 9 : 6}
                  fill={scopeColor[record.scope]}
                  className={cn("transition-all", isHovered && "drop-shadow-[0_0_8px_currentColor]")}
                  style={{ color: scopeColor[record.scope] }}
                />
                <text
                  x={pos.x}
                  y={pos.y + (pos.y > center ? 20 : -12)}
                  textAnchor="middle"
                  className={cn(
                    "fill-content-muted text-[10px] transition-opacity",
                    isHovered ? "opacity-100 fill-content-primary font-medium" : "opacity-70"
                  )}
                >
                  {truncate(record.key, 18)}
                </text>
              </motion.g>
            );
          })}
        </svg>
      </div>
      {hovered != null && (
        <div className="glass-ambient rounded-lg border border-hairline p-3 text-sm">
          <p className="font-medium text-content-primary">{shown[hovered].key}</p>
          <p className="mt-1 text-content-secondary">{truncate(shown[hovered].content, 200)}</p>
        </div>
      )}
      <div className="flex flex-wrap gap-3 text-xs text-content-muted">
        {(Object.keys(scopeColor) as MemoryScope[]).map((scope) => (
          <span key={scope} className="flex items-center gap-1.5">
            <span className="h-2 w-2 rounded-full" style={{ backgroundColor: scopeColor[scope] }} />
            {scope}
          </span>
        ))}
      </div>
    </div>
  );
}
