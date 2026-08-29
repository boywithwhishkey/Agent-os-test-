# DEFERRED GOALS — genuinely future/optional, not current blockers

Anything here is intentionally out of scope for the current push. Do not
treat these as blockers or as reasons to delay 10_NEXT_STEPS.md items.
Remove an item from this file the moment it's actually implemented —
don't leave completed work listed here.

## Workflow builder — flagship-level polish

- Node toolbar (contextual actions on a selected node without opening the
  modal dialog).
- Context side panel for editing a step in place, instead of the current
  modal dialog.
- Execution-pulse animation that visibly travels along an edge while a
  connected step is running (currently: nodes glow, edges are statically
  animated/violet, but there's no traveling pulse tied to live run state).
- Per-node inline validation-error highlighting (currently: a single list
  of validation errors rendered above the canvas).
- Additional keyboard interactions beyond delete (e.g. arrow-key node
  nudging, multi-select via marquee, copy/paste steps).

## Broader premium motion pass

A dedicated animation/visual-direction pass (beyond what already exists
from prior sessions) for:
- Orchestration: animated researcher → builder → reviewer flow with
  connecting-line and active-step-pulse visualization.
- Autonomous runs: parallel-specialist visualization, planner/verifier/
  synthesis state animation, live job cards.
- Memory: similarity-score visual ranking, graph/network-style view of
  related memories.
- Runtime: circuit-breaker state diagram, rate-limit gauge visualization.
- Audit: a timeline view mode as an alternative to the table.
- System Health: a visual service-dependency map (API/DB/Redis/LLM/queue
  nodes with animated health-check pulses).

## Integrations / connectors

- Additional connector adapters beyond n8n (e.g. Slack, generic webhook,
  email) — **do not add these speculatively**; only build a new adapter
  when there's a concrete product need for it. The adapter architecture
  (`IntegrationAdapter` base class + factory registry in
  `app/integrations/`) is already designed to make this a clean addition
  when the time comes.
- Persisting integration status/history durably (currently in-memory/
  process-local, reset on backend restart) — only worth doing once
  Postgres is actually configured in production.

## Persistence / infra

- Durable Postgres/Redis backends in production — this becomes a current
  blocker (not deferred) once `DATABASE_URL`/`REDIS_URL` are provided; see
  10_NEXT_STEPS.md and 02_CURRENT_STATE.md "NEEDS CREDENTIALS". Until then
  it stays here as a scoped-out nice-to-have.
- Setting `environment: production` in the live `/health` response
  (currently reports `development`) — cosmetic, low priority.

## Non-essential cleanup

- Renaming internal, non-user-facing identifiers that still say "Agent
  OS" (Python distribution name in `pyproject.toml`, frontend
  `package.json` `"name": "agent-os-frontend"`, historical `PHASE*_
  INTEGRATION.md` files, `README.md`). These don't affect users or brand
  presentation; rename only opportunistically, never as a dedicated task.
- Optimizing frontend bundle size (`Workflows` chunk is ~195KB / 63KB
  gzipped, `index` chunk ~390KB / 124KB gzipped) — not currently a
  reported problem, revisit only if load-time becomes a concern.
