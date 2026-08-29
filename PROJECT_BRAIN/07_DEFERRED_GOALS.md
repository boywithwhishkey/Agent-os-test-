# DEFERRED GOALS — genuinely future/optional, not current blockers

Anything here is intentionally out of scope for the current push. Do not
treat these as blockers or as reasons to delay 10_NEXT_STEPS.md items.
Remove an item from this file the moment it's actually implemented —
don't leave completed work listed here.

## Workflow builder — flagship-level polish

- Context side panel for editing a step in place, instead of the current
  modal dialog. (Node toolbar, execution-pulse-along-edge, and per-node
  validation highlighting are DONE — see 02_CURRENT_STATE.md.)
- Additional keyboard interactions beyond delete (e.g. arrow-key node
  nudging, multi-select via marquee, copy/paste steps).

## Broader premium motion pass

Only two items remain from the original animation/visual-direction list:
- Runtime: a circuit-breaker state *diagram* / execution timeline view as
  a richer alternative to the current live badge + rate-limit gauge
  (which ARE done — see 02_CURRENT_STATE.md).
- Audit: correlation-ID quick-copy — needs a Postgres migration to add a
  `correlation_id` column to `tool_audit_events` plus threading a
  correlation id through `ToolExecutor`/`ToolExecuteRequest`; do this once
  `DATABASE_URL` exists and can be tested against for real (timeline view
  mode itself is DONE — see 02_CURRENT_STATE.md).
- Agents, Approvals, Tools have not had a dedicated additional animation
  pass beyond the pre-existing design system — lower priority since they
  already use the shared Card/Badge/StatusBadge/skeleton components
  consistently.

Done this session (removed from this list): Orchestration's researcher →
builder → reviewer connected-node visualization
(`OrchestrationPipeline.tsx`); System Health's persistence/LLM service
map; Audit's table/timeline view toggle; Workflows' node toolbar,
execution-pulse edges, and validation highlighting; Autonomous's real
parallelism badge + grid layout; Memory's relationship graph view.

## Integrations / connectors

- A session following CLAUDE.md's explicit "finish everything possible
  without new credentials" directive added real read/verify adapters for
  Gemini, PostgreSQL, Redis, OpenAI, Anthropic, Cloudflare, and Render,
  plus a full OAuth2 authorize/callback/disconnect flow for GitHub — see
  02_CURRENT_STATE.md. The remaining 11 OAuth catalog entries (Slack,
  Notion, Gmail, Google Calendar, Google Drive, GitLab, Jira, HubSpot,
  Salesforce, Dropbox, OneDrive) follow the exact same pattern as GitHub
  (`app/integrations/oauth/config.py` + two Settings fields +
  `implemented=True` on the CatalogSpec) — **still don't add these
  speculatively**; do the next one only when there's a concrete product
  need or the operator actually wants to connect that account. Google's
  three entries (gmail/calendar/drive) can likely share one OAuth app/
  client id with different `scope` strings — verify this before assuming
  three separate client id/secret pairs are needed.
- `execute()` is intentionally "not supported" on every non-webhook
  adapter added this session (OpenAI, Anthropic, Cloudflare, Render,
  GitHub, Gemini, Postgres, Redis) — they only verify identity/
  reachability. Wiring real actions (e.g. GitHub "open an issue",
  Cloudflare "deploy a Pages project") onto the generic `execute()`
  interface is deferred until there's a concrete workflow that needs it;
  don't build actions speculatively.
- Persisting integration status/history and OAuth tokens durably
  (currently in-memory/process-local, reset on backend restart) — only
  worth doing once Postgres is actually configured in production. Note
  for whoever does this: OAuth access tokens would need encryption at
  rest, not just a plain column — don't persist them in cleartext.

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
