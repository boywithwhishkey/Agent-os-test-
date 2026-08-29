import { BaseEdge, getSmoothStepPath, type EdgeProps } from "@xyflow/react";

export interface PulseEdgeData extends Record<string, unknown> {
  active?: boolean;
}

/** A smoothstep edge with an optional traveling dot for "data is flowing here right now". */
export function PulseEdge({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style,
  markerEnd,
  data,
}: EdgeProps) {
  const [edgePath] = getSmoothStepPath({ sourceX, sourceY, sourcePosition, targetX, targetY, targetPosition });
  const active = Boolean((data as PulseEdgeData | undefined)?.active);

  return (
    <>
      <BaseEdge id={id} path={edgePath} markerEnd={markerEnd} style={style} />
      {active && (
        <circle r="4" fill="var(--color-accent-blue)" style={{ filter: "drop-shadow(0 0 4px var(--color-accent-blue))" }}>
          <animateMotion dur="1.1s" repeatCount="indefinite" path={edgePath} />
        </circle>
      )}
    </>
  );
}
