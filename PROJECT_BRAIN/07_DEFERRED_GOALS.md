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

- Runtime: a circuit-breaker state *diagram* / execution timeline view as
  a richer alternative to the current live badge + rate-limit gauge
  (which ARE done — see 02_CURRENT_STATE.md).
- ~~Audit: correlation-ID quick-copy~~ **DONE 2026-08-31** — migration 006,
  threaded through `ToolExecutor`, exposed in the API and the Audit drawer,
  verified against a real PostgreSQL. See 02_CURRENT_STATE.md.
- Agents, Approvals, Tools have not had a dedicated additional animation
  pass beyond the shared glass/motion design system (see next item) —
  lower priority since they already use the shared Card/Badge/
  StatusBadge/skeleton components consistently, which now inherit the
  glass treatment automatically.

Done this session (removed from this list): Orchestration's researcher →
builder → reviewer connected-node visualization
(`OrchestrationPipeline.tsx`); System Health's persistence/LLM service
map; Audit's table/timeline view toggle; Workflows' node toolbar,
execution-pulse edges, and validation highlighting; Autonomous's real
parallelism badge + grid layout; Memory's relationship graph view.

## THYNACT glass/motion design-system — bespoke follow-ups

A shared foundation (glass material system, `AmbientBackground`,
`lib/motion.ts` tokens, `ScrollReveal`/`StaggerGroup`) now covers the whole
product via `Card`/`MetricCard`, plus a full bespoke pass on Dashboard and
hand-touches on `AgentCard`/`ConnectorCard`/`StepNode`/`Drawer`/`Dialog`/
`CommandPalette`/`AppShell`/`Sidebar`/`Topbar` — see 00_START_HERE.md and
02_CURRENT_STATE.md. What's genuinely deferred (do these only as a
focused follow-up, not speculatively):
- **Orchestration**: the original brief's "animated data flow / execution
  particles / active-node energy" beyond the existing
  `OrchestrationPipeline` connected-node view. Only add particle/flow
  animation that reflects real per-step state — the backend orchestration
  call is still a single synchronous request with no incremental status,
  so don't fabricate in-flight motion that implies granularity the API
  doesn't provide.
- **Autonomous**: visualizing planner/specialists/verifier/synthesis as an
  "evolving computation graph" (parallel specialists visibly separating
  and converging) — currently a staggered grid, not a graph layout.
- **Memory**: spatial/semantic-similarity-driven graph movement beyond the
  current shared-field relationship graph (`MemoryGraph.tsx`) — still
  blocked on there being no real memory-to-memory similarity score from
  the API (see the existing DONE note); don't fabricate one.
- **Workflows**: edge glow/pulse refinement beyond the existing
  `PulseEdge`, minimap polish, and a floating configuration drawer to
  replace the modal step editor (this last one is also listed under
  "Workflow builder — flagship-level polish" above; don't duplicate the
  work, do it once).
- **Integration Hub connector tiles**: provider-specific "subtle glow" per
  connector type beyond the shared `ConnectorCard` glass treatment.
- All of the above are optional visual depth, not correctness work — never
  let them block or complicate a real feature/bugfix.

## Ambient background palette — optional extensions

Two sessions ago the ambient/background system (only — not interactive
accents) was retinted to a gold/deep-red direction; the next session
replaced that with a more specific cream/bronze/deep-navy reference
palette (`--color-ambient-cream`/`-bronze`/`-navy`, see 00_START_HERE.md
and 02_CURRENT_STATE.md HEAD `8a9dd81`) — treat cream/bronze/navy as
current, gold/red as superseded/stale if you see it referenced anywhere
old. Both passes deliberately left interactive accents (buttons, links,
nav active state, the BrandMark wordmark gradient) violet/blue, since
neither brief's background section asked for a full brand recolor and
that's a bigger identity decision than either pass warranted. If a future
session is explicitly asked to extend the cream/bronze/navy direction
further (e.g. into BrandMark or primary buttons), do it as its own
deliberate scoped task, not as a side effect of an unrelated change — and
keep the `ambient-*` tokens (decorative) and `--color-accent-red`
(status: error/offline) separate regardless.
- `ScrollReveal` was only added to the Integrations page's "All
  integrations" section (the largest block) — Currently
  integrated/Ready to connect/Popular don't have it yet. Low priority:
  the page already gets a page-level enter animation from `AppShell`.

## Integrations / connectors

- Real read/verify adapters exist for Gemini, PostgreSQL, Redis, OpenAI,
  Anthropic, Cloudflare and Render, plus a generic OAuth2 authorize/callback/
  disconnect framework. **Corrected 2026-08-31:** GitHub is no longer the only
  OAuth connector — **Slack, Notion and GitLab OAuth configs already exist in
  `app/integrations/oauth/config.py` with Settings fields and tests, and a
  Make webhook adapter exists too.** Earlier versions of this file described
  Slack/Notion as speculative future work; that was stale. They are
  implemented-but-unconfigured (AUTH_REQUIRED / CREDENTIAL_REQUIRED), not
  missing. Live catalog as of 2026-08-31: 28 entries, 13 implemented, 2
  LIVE_VALIDATED (postgresql, redis).
  The remaining OAuth catalog entries (Gmail, Google Calendar, Google Drive,
  Jira, HubSpot, Salesforce, Dropbox, OneDrive) follow the same pattern —
  **still don't add these speculatively**; do the next one only when there is a
  concrete product need or the operator actually wants that account connected.
  Google's three entries can likely share one OAuth app with different `scope`
  strings — verify before assuming three client id/secret pairs.
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


## Free-tier production infrastructure — decide before 2026-10-02

Deferred, not forgotten: the production datastores created on 2026-09-02 are
free-plan and are **not** production durability on their own.

- `dpg-dabo2bqfngtc73eogac0-a` (PostgreSQL 16) has `expiresAt: 2026-10-02`.
  Render deletes free databases 30 days after creation. Cheapest paid plan in
  the Render MCP enum is `basic_256mb`.
- `red-dabo2eifngtc73eoghkg` (Key Value) runs `persistenceMode: off`, so it has
  no Redis-side persistence at all: queued jobs do not survive a Redis restart
  even once `REDIS_URL` is wired. Cheapest paid plan in the enum is `starter`.

The Render MCP does **not** expose pricing, so no figures are recorded here
rather than guessing them. This is a billing decision and is deliberately left
to the operator; the free pair is still worth wiring up first because it proves
the whole cutover end to end at zero cost.
