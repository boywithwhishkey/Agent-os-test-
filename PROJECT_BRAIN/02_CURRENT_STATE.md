# CURRENT STATE — verified as of 2026-08-29, HEAD `87d32a1`

This file records only what has been directly verified against the
repository (tests, source, live production checks) as of the commit above.
If a later session changes any of this, update this file — don't append a
contradicting note elsewhere.

## PRODUCTION STATUS

- **Live frontend:** https://app.thynact.com — HTTP 200. Repeatedly
  verified throughout this session (most recently at HEAD `ec554d6`) that
  the served `index.html` asset hashes match a fresh local `pnpm build`
  byte-for-byte — Cloudflare Pages deploys `origin/main` correctly,
  usually within ~1-2 minutes of a push. Re-verify this the same way after
  any future push: `pnpm build` locally, then compare
  `dist/assets/index-*.{js,css}` filenames against what
  `curl https://app.thynact.com/` serves.
- **Live API:** https://api.thynact.com — `/health` returns
  `{"status":"ok","service":"THYNACT","environment":"development"}` (HTTP 200).
  `/ready` returns `{"status":"ready","checks":{}}` (HTTP 200). The empty
  `checks` object is expected/correct: it means every backend (memory/queue)
  is currently set to `memory`, so there's nothing to health-check yet (see
  PERSISTENCE below).
- `environment: "development"` in the live `/health` response — the Render
  service does not have `AGENT_OS_APP_ENV`/environment override set to
  `production`. Cosmetic, not a functional blocker. UNVERIFIED whether this
  is intentional.
- Auth is live and enforced: unauthenticated `GET /api/v1/integrations`
  returns `401 {"detail":"Unauthorized"}` (not `503`), which means
  `AGENT_OS_API_KEY` **is** configured on the Render production service.
  This session does not have that key's value and cannot exercise
  authenticated endpoints against production directly — see "NEEDS
  CREDENTIALS" and 10_NEXT_STEPS.md.

## Environment note

Mid-session, `git push origin main` failed once with "Invalid username or
token" from the Replit-managed git askpass helper (`replit-git-askpass`),
even though `gh auth status` showed a valid, active GitHub CLI login with
`repo` scope. Fixed by running `gh auth setup-git` (routes git's credential
resolution through the already-authenticated `gh` CLI) and retrying — no
secrets were exposed, nothing destructive was done. If a future session
hits the same "Invalid username or token" push error, try this first
before assuming a deeper auth problem.

Also: a broad `find / -iname ...` (or `bfs`-backed) filesystem-wide search
launched in the background can run for over an hour and grow to several
GB of RSS on this box, eventually starving memory (observed: 7.6/7.8GB
used, causing frontend test timeouts that looked like flaky/broken tests
but were actually system thrashing). If frontend tests suddenly start
timing out with no related code change, check `free -h` and `ps aux
--sort=-%mem` before assuming a regression — kill any stray `find`/`bfs`
process consuming outsized memory (safe: read-only, no side effects) and
retest. Avoid unscoped `find /` entirely; scope searches to specific
directories.

## DONE (verified this session)

- **CORS fix (critical production bug).** Backend previously only allowed
  `Content-Type, Authorization` in CORS preflight, but the frontend sends
  `X-API-Key` and `X-Correlation-ID` on every request — every authenticated
  browser call to production was silently blocked by the browser. Fixed in
  `app/main.py` (`allow_headers` now includes `X-API-Key`/`X-Correlation-ID`,
  plus `expose_headers=["X-Correlation-ID"]` so the frontend can read the
  server-assigned correlation id cross-origin). Verified live: preflight
  `OPTIONS /api/v1/tasks` from `Origin: https://app.thynact.com` now returns
  `200` with the right `access-control-allow-headers`. Regression tests added
  in `tests/test_health.py`.
- **Connector registry.** Integrations previously only exposed a raw
  `POST /api/v1/integrations/execute` with no visibility into configuration
  or health. Added `GET /api/v1/integrations` (per-provider configured/
  connected/last-check/last-execution state) and
  `POST /api/v1/integrations/{provider}/test` (a real reachability probe —
  not a faked success) in `app/api/phase9.py`, backed by
  `app/integrations/status_store.py` (in-memory, process-local — this is
  operational telemetry, not durable state). Frontend `Integrations.tsx`
  rewritten as a connector gallery driven by this data, with a
  "Test connection" action and honest "not configured — set `N8N_BASE_URL`"
  messaging when unconfigured. Backend tests:
  `tests/test_phase9_integrations_registry.py` (6 tests). Frontend tests:
  `frontend/src/pages/Integrations.test.tsx` (2 tests).
- **THYNACT branding.** Renamed the product surface from "Agent OS" to
  THYNACT across the frontend (sidebar, dashboard, settings, command
  palette, page copy, `<title>`/meta) and the backend `/health` service
  name (`app/core/config.py` `app_name` default). New reusable
  `frontend/src/components/ui/BrandMark.tsx` (icon/wordmark/tagline, 3
  variants: `mark`/`compact`/`full`). One tasteful brand moment on the
  Dashboard with the tagline "Built to Think. Powered to Act." plus
  supporting line "From intelligence to execution." Verified live in
  production `/health` response and in the deployed frontend bundle.
- **API Online heartbeat indicator.** Rewrote
  `frontend/src/components/layout/HealthIndicator.tsx`:
  - **Online** = green dot, double-beat scale animation
    (`animate-heartbeat`, ~1.8s cycle) + an absolutely-positioned expanding
    ring (`animate-heartbeat-ring`) that fades out — ring never shifts
    layout since it's `position: absolute` inside a fixed-size wrapper.
  - **Connecting** = amber dot, gentle breathing opacity/scale
    (`animate-breathe`, ~2.2s).
  - **Offline** = red dot, slow static-friendly pulse (existing
    `animate-pulse-slow`, ~2.4s) — no aggressive flashing.
  - All three are CSS keyframes added to `frontend/src/index.css`'s
    `@theme` block, so the pre-existing global
    `@media (prefers-reduced-motion: reduce)` rule (forces
    `animation-duration: 0.01ms` on everything) neutralizes them
    automatically — no extra reduced-motion logic needed.
- **Workflow builder visual polish.** `StepNode.tsx`: running/
  waiting-on-approval nodes get a soft status-colored glow (blue/amber
  `box-shadow` + the existing pulse/breathe keyframes), scoped only to
  those two states. `Workflows.tsx`: `defaultEdgeOptions` now gives every
  edge (not just freshly-drawn ones) a `smoothstep` curve + animated violet
  stroke. Status-aware node styling (icons/colors per `StepStatus`) already
  existed from a prior session and was preserved as-is.
- **n8n `test_connection()` test coverage.** Added
  `httpx.MockTransport`-based tests in `tests/test_phase9_n8n.py` covering
  reachable-host, timeout, and network-error outcomes — previously only
  the route layer was covered (via a fake adapter).
- **Orchestrate pipeline visualization.** New
  `frontend/src/components/agents/OrchestrationPipeline.tsx`: a compact
  connected-node view of the fixed researcher → builder → reviewer roles,
  with a status ring per step (pending/running-glow/success/failed) and a
  violet progress line that fills between completed steps. Deliberately
  only renders from the final per-job result, not fabricated in-flight
  step tracking — the backend orchestration call is a single synchronous
  request with no incremental per-step status while pending.
- **Real hybrid-search relevance scores in Memory.** The semantic memory
  service (`app/memory/semantic.py`) already computed a real weighted
  score (semantic + lexical + importance) per ranked result but discarded
  it before returning from `/api/v1/memory/search`. Now attached as
  optional `score`/`semantic_score`/`lexical_score` fields on
  `MemoryRecord` (additive — existing writes/reads unaffected) and
  rendered as a match-percentage bar on the Memory search page. Note: the
  raw `score` can slightly exceed 1.0 due to an importance bonus term in
  the ranking formula — the frontend clamps it to 0–100% for display.
- **Real circuit-breaker/rate-limit visibility in Runtime.** Added
  read-only `CircuitBreaker.status(key)` and
  `SlidingWindowRateLimiter.usage(key)` getters (neither mutates state) and
  a new `GET /api/v1/runtime/status?provider=&workflow=` route. The
  Runtime page shows a live circuit-breaker badge (with recovery countdown
  when open) and a rate-limit usage gauge, polling every 15s.
- **Persistence/LLM visibility in System Health.** `/health` now also
  returns `llm_provider` and a `backends` map (memory/task/workflow/
  runtime/tool/queue → which backend each is using). System Health has a
  new "Persistence map" card visualizing durable (postgres/redis) vs
  ephemeral (memory) per subsystem.
- **Audit timeline view.** Added a Table/Timeline segmented toggle to the
  Audit Logs page — pure frontend, reuses the existing
  `/api/v1/tools/audit` data, no backend change. Correlation-ID
  quick-copy (also requested for Audit) is genuinely deferred: the
  `tool_audit_events` table/dataclass has no `correlation_id` field at
  all, so adding it needs a Postgres migration plus threading a
  correlation id through `ToolExecutor`/`ToolExecuteRequest` — not done
  blind without a real database to test the migration against (this repo
  has no `DATABASE_URL` available to this session).
- **Workflows flagship features (3 of 4).** Per-node validation
  highlighting (`invalidStepIds()` parses which step id a validation
  error names, that node gets a dashed red ring); a node toolbar
  (React Flow's built-in `NodeToolbar`, shown on selection, with Edit/
  Delete); execution-pulse-along-edge (`PulseEdge.tsx`, a small dot
  traveling via native SVG `animateMotion` whenever the connected step's
  live run status is "running" — real state, not fabricated). The context
  side panel (4th item) is intentionally not done — the existing modal
  step editor works well and replacing it is a bigger UX change than this
  pass warranted.
- **Autonomous Runs: real parallelism badge + grid layout.** Exposed
  `settings.max_parallel` (the real `asyncio.Semaphore` limit gating
  concurrent specialist execution) on `/health`. Autonomous now shows a
  "Up to N in parallel" badge and renders specialist jobs as a
  staggered-entrance grid instead of a vertical stack.
- **Memory relationship graph.** New List/Graph toggle on Memory search.
  The graph is a circular node-link diagram (`MemoryGraph.tsx`) where
  edges are drawn only from genuinely shared fields (tag/project_id/
  task_id) between records in the current result set — there is no
  memory-to-memory similarity score available from the API (only
  query-to-record relevance), so this deliberately doesn't fabricate one.
- **Backend test suite: 137/137 passing** (`uv run pytest tests/ -q`).
- **Frontend: 25/25 tests passing** (`pnpm test`) — test count unchanged
  since the last update because MemoryGraph has no dedicated test file
  yet (rendered/exercised indirectly through Memory page usage only).
  **Typecheck clean**
  (`pnpm typecheck`), **lint clean** — 0 errors, 2 pre-existing warnings
  unrelated to this session's changes (`Toast.tsx`, `theme.tsx`,
  `react-refresh/only-export-components`), **production build clean**
  (`pnpm build`).

## PARTIAL

- **Workflow builder** is functional and has 3/4 flagship features (node
  toolbar, validation highlighting, execution-pulse edges — see DONE
  above); only the context side panel (editing is still a modal dialog,
  deliberately) is not done.
- **Premium motion pass** has been done this session for: Dashboard (brand
  moment), API heartbeat, Workflows canvas, Orchestrate (pipeline
  visualization), Memory (match-score bar + relationship graph), Runtime
  (circuit-breaker/rate-limit gauges), System Health (persistence map),
  Audit (timeline view), Autonomous (parallelism badge + grid). Remaining:
  Agents (static/informational by design — see per-subsystem table),
  Approvals, Tools. These still use the pre-existing (already reasonably
  polished) design system from prior
  sessions without a dedicated additional pass.
- **n8n connector completeness audit (this session):** verified
  registration, config validation (`is_provider_configured`), the
  test-connection endpoint, auth header handling, timeout handling,
  correlation-ID passthrough (`X-Agent-OS-Correlation-ID`), network-failure
  handling, non-2xx handling, and non-JSON response body handling
  (`tests/test_phase9_n8n.py` — added the missing non-JSON test this
  session) — all covered by tests. Frontend configured/unconfigured state
  and execution UI were built in an earlier session and are unchanged.
  n8n itself is genuinely production-ready code-wise; it is NOT CONFIGURED
  in production (no `N8N_BASE_URL`) and reports that honestly rather than
  faking a connection — see PRODUCTION DEPENDENCY / CREDENTIAL AUDIT.

## BLOCKED (this session, environment-limited — not code issues)

- **No interactive browser tooling connected.** Claude-in-Chrome was not
  available this session. All frontend verification was via `vitest`
  (jsdom), `tsc`, `eslint`, `vite build`, and `curl`-level checks
  (index.html + asset fetch, `/health`, `/ready`, CORS preflight headers).
  Full interactive QA (click-through every page, browser console errors,
  live network tab, actual responsive rendering at 375/430/768/820/1024/
  1180/1440px) has **not** been performed.
- **No production API key available to this session.** Confirmed one is
  configured on Render (`401` not `503` on protected routes), but its value
  isn't available here, so authenticated production flows (create task,
  orchestrate, autonomous run, tools/approvals, audit, memory, workflow
  run, runtime execution, integration execute) could not be exercised
  end-to-end against the **live** API. They are however fully covered by
  the local backend test suite, which exercises the same code paths
  in-process (137 tests, all passing).

## PRODUCTION DEPENDENCY / CREDENTIAL AUDIT

Full inventory of every external dependency for non-mock production, as of
this session. Never print secret values — names and status only.

| Service | Purpose | Env var(s) | Required/Optional | Current status (verified live) | Falls back to | How to verify after configuring |
|---|---|---|---|---|---|---|
| Operator auth | Gates every `/api/v1/*` route | `AGENT_OS_API_KEY` | **Required** for any protected call | **SET on Render** — confirmed live: unauthenticated calls return `401`, not `503` (`503` is what `require_api_key` returns when the var is unset) | `503 "API authentication is not configured"` if unset | `curl -H "X-API-Key: <key>" https://api.thynact.com/api/v1/tools` → expect `200` |
| PostgreSQL | Durable storage for tasks/approvals/audit/workflow defs & runs/runtime executions/memory | `DATABASE_URL` | Optional (falls back cleanly) | **NOT set** — `/health` `backends` map shows every subsystem as `memory`; `/ready` has no `database` check (only appears when a backend is set to `postgres`) | All state lives in the FastAPI process's memory — lost on every restart/redeploy | After setting `DATABASE_URL` **and** flipping the relevant `AGENT_OS_*_BACKEND` vars to `postgres`: run `python scripts/migrate.py` once, then `curl https://api.thynact.com/ready` → expect a `"database": "ok"` check |
| Redis | Durable job queue | `REDIS_URL` | Optional (falls back cleanly) | **NOT set** — `backends.queue` is `memory` | In-memory queue (`InMemoryJobQueue`) — no cross-process/durable queueing | After setting `REDIS_URL` and `AGENT_OS_QUEUE_BACKEND=redis`: `curl https://api.thynact.com/ready` → expect a `"queue": "ok"` check |
| n8n | Webhook-based workflow/integration execution | `N8N_BASE_URL` (required to enable), `N8N_WEBHOOK_PREFIX` (optional, default `webhook`), `N8N_WEBHOOK_AUTH_HEADER` + `N8N_WEBHOOK_AUTH_VALUE` (optional, only if the n8n instance requires auth) | Optional | **NOT set** — confirmed via code path (`is_provider_configured` checks `settings.n8n_base_url` truthiness); the Integrations page reports "Not configured" and names `N8N_BASE_URL` | `GET /api/v1/integrations` reports `configured: false`; `POST /api/v1/integrations/n8n/test` returns `503` naming the missing var; `POST /api/v1/integrations/execute` returns `400` | Set `N8N_BASE_URL`, then use the "Test connection" button on the Integrations page (or `POST /api/v1/integrations/n8n/test`) → expect `connected: true` with a real latency figure |
| LLM provider | Powers orchestration/autonomous specialist reasoning | `AGENT_OS_LLM_PROVIDER` (`mock` or `gemini`), `AGENT_OS_LLM_MODEL`, `GEMINI_API_KEY` | Optional (mock works fully, just isn't a real model) | **CONFIRMED `mock`** in production — `/health` now returns `"llm_provider": "mock"` directly (previously unverified; this session added that field so it no longer has to be inferred) | Deterministic mock responses from `app/llm/mock.py` — orchestration/autonomous flows work end-to-end but outputs aren't real LLM reasoning | Set `GEMINI_API_KEY` and `AGENT_OS_LLM_PROVIDER=gemini`, then `curl https://api.thynact.com/health` → expect `"llm_provider": "gemini"`, and run an orchestration to confirm real model output |
| CORS allowlist | Which origins may call the API from a browser | `AGENT_OS_CORS_ORIGINS` | Required (has a working default) | **SET correctly** — verified live: preflight from `https://app.thynact.com` succeeds (`200`), preflight from an arbitrary origin (`https://evil-example.com`) is rejected (`400`, no `Access-Control-Allow-Origin` reflected) | Defaults to a hardcoded list already including `https://app.thynact.com` (see `app/core/config.py`) | Preflight `OPTIONS` from the origin in question and check `access-control-allow-origin` in the response |

## PERSISTENCE MAP

Every one of these is currently **`memory`** (ephemeral, process-local, lost
on restart) in production, confirmed via the live `/health` `backends` map:

| Data | Backend setting | Current value |
|---|---|---|
| Tasks | `AGENT_OS_TASK_BACKEND` | `memory` |
| Approvals & tool audit | `AGENT_OS_TOOL_BACKEND` | `memory` |
| Memory (semantic/lexical) | `AGENT_OS_MEMORY_BACKEND` | `memory` |
| Workflow definitions | `AGENT_OS_WORKFLOW_DEFINITION_BACKEND` | `memory` |
| Workflow runs | `AGENT_OS_WORKFLOW_BACKEND` | `memory` |
| Runtime executions | `AGENT_OS_RUNTIME_BACKEND` | `memory` |
| Job queue | `AGENT_OS_QUEUE_BACKEND` | `memory` |

This is reported honestly, not hidden: `/ready` shows an empty `checks: {}`
(correct — there's nothing to health-check when everything is `memory`),
and the System Health page's "Persistence map" card visually marks every
one of these "Ephemeral" rather than implying durability. The
`postgres`/`redis` code paths exist and are unit-tested (with fakes), but
have never run against a real Postgres/Redis instance in any session with
access to this repo — see 00_START_HERE.md's migration note.

## AUTH / CORS BOUNDARY — VERIFIED LIVE THIS SESSION

- No API key → `401 {"detail":"Unauthorized"}` (not `503`, confirming the
  key **is** configured server-side).
- Wrong API key → `401` (generic, doesn't leak whether the key was close).
- Unknown route → `404 {"detail":"Not Found"}`.
- CORS preflight from `https://app.thynact.com` → `200`, correct
  `access-control-allow-headers` including `X-API-Key`/`X-Correlation-ID`.
- CORS preflight from an arbitrary non-allowlisted origin
  (`https://evil-example.com`) → `400`, origin **not** reflected — the
  allowlist is real, not a wildcard.
- What remains unverified: actual authenticated business-logic flows
  (create task, run orchestration, etc.) against the **live** API, since
  this session has no valid `AGENT_OS_API_KEY` value. These are fully
  covered by the local backend test suite instead (137 tests, in-process,
  same code paths).

## RESPONSIVE QA — STATIC REVIEW DONE, INTERACTIVE STILL BLOCKED

No browser automation tool was available this session, so this is a
code-level review, not a rendered/visual one. Findings:
- Both data tables (`WorkflowRuns.tsx`, `Audit.tsx`) that use a
  `min-w-[...]` are correctly wrapped in `overflow-x-auto` containers —
  no horizontal page overflow risk.
- `MemoryGraph.tsx`'s fixed-width SVG is also wrapped in `overflow-x-auto`
  with `max-w-full` on the element itself.
- `Drawer.tsx` uses `w-full max-w-md` (full-width on mobile, capped on
  larger screens) with an internal `overflow-y-auto` content area — no
  overflow or clipping risk found.
- `AppShell.tsx` has `overflow-x-hidden` at the root plus `min-w-0` on the
  flex content column — the standard fix for flex-child overflow.
- No other hardcoded pixel widths found outside of small fixed-size UI
  chrome (sidebar width, icon badges) that wouldn't be expected to scale.
- **No genuine defect found in this pass** — nothing was "fixed" here
  because nothing broken was found this way. This does **not** replace
  actual interactive verification at the 7 target breakpoints (375/430/
  768/820/1024/1180/1440), especially real touch/drag behavior on the
  Workflows React Flow canvas, which cannot be assessed by reading code —
  that remains genuinely blocked on browser tooling.

## Per-subsystem status

| Subsystem | Status | Notes |
|---|---|---|
| Dashboard | DONE (this session: brand moment added) | Metrics, recent audit, quick actions, session activity — all backed by real queries |
| Tasks | DONE (prior session) | Create/retrieve, validation, error states — covered by `Tasks.test.tsx` + backend tests |
| Orchestration | DONE, motion pass DONE | researcher/builder/reviewer roles + `OrchestrationPipeline` connected-node visualization (this session) |
| Autonomous | DONE, motion pass DONE | planner/specialists/verifier/synthesis, real "Up to N in parallel" badge + staggered grid layout (this session) |
| Agents | DONE, UI-only by design | Static/informational cards — there is no backend agent registry endpoint; agents are roles invoked through orchestration/autonomous runs, not standalone listable entities |
| Workflows | DONE, 3/4 flagship features done | Validation highlighting, node toolbar, edge pulse (this session); context side panel still deferred |
| Workflow Runs | DONE (prior session) | Run details, resume, persistence via workflow backend |
| Approvals | DONE (prior session) | Single-use pre-authorized grants (not a pending-request queue by design) |
| Memory | DONE, motion pass DONE | Semantic + lexical search, context, filters, delete, real match-score bar, staggered result animation, and a shared-field relationship graph view (this session) |
| Runtime | DONE, motion pass PARTIAL | Execute/retries/rate-limit/circuit-breaker/idempotency, live circuit-breaker badge + rate-limit gauge (this session); no execution timeline view yet |
| Tools | DONE (prior session) | List/execute/risk levels/approval-required/audit |
| Integrations | DONE (this session) | Connector registry + test-connection, n8n only, extensible adapter architecture |
| Audit | DONE, motion pass DONE | Tool events, status, timestamps, table + timeline views (this session). No correlation ID on audit events yet — see NEEDS CREDENTIALS/DATABASE_URL, this requires a migration |
| Health | DONE | Live `/health` + `/ready` + persistence/LLM service map (this session) |
| Settings | DONE (this session: About/brand section added) | API base URL + key (sessionStorage only), theme, About |
| Persistence | PARTIAL — production is memory-only | Code supports Postgres/Redis backends (`app/persistence/`, `app/queue/redis_queue.py`) but production has none configured (see NEEDS CREDENTIALS) |
| Responsive UI | UNVERIFIED at real breakpoints | Codebase has solid responsive primitives (`overflow-x-hidden`, `min-w-0`, mobile sidebar drawer, responsive grids) but has not been checked in an actual browser at the 7 target breakpoints this session |
