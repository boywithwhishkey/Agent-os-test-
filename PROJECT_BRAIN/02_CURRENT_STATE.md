# CURRENT STATE — verified as of 2026-08-31, HEAD `1b5ccc6`

This file records only what has been directly verified against the
repository (tests, source, live production checks) as of the commit above.
If a later session changes any of this, update this file — don't append a
contradicting note elsewhere.

## SESSION 2026-08-31 — FIRST REAL POSTGRES/REDIS/pgvector VALIDATION

Everything in this section was verified by running it, not by reading code.
This session also converted the durable operating rules into root `CLAUDE.md`
plus two scripts, so future sessions no longer need a giant pasted prompt.

### Environment is now genuinely ready (Claude cloud)

- `scripts/bootstrap_claude_cloud.sh` (new, idempotent) and
  `scripts/project_doctor.sh` (new, report-only) — both executed successfully,
  and bootstrap was re-run to prove it is a no-op second time.
- Python: `uv sync --extra dev --frozen` → venv on **3.12.3** (system `python3`
  is 3.11 — always `uv run`). Frontend: `pnpm install --frozen-lockfile` (pnpm
  resolved 10.26.1 via `packageManager`).
- **Docker has no daemon here** (`/var/run/docker.sock` absent). `infra/`
  compose files are untouched and still valid for other environments; native
  services are the right path in Claude cloud.

### PostgreSQL + pgvector + Redis — REAL, first time in this project's history

- **pgvector was genuinely missing** and is a hard requirement (migrations 001
  and 002 `CREATE EXTENSION vector`, use a `vector` column and build an HNSW
  index). Installed `postgresql-16-pgvector` **0.6.0**. Note `apt-get update`
  is required first — the preinstalled lists 404.
- Dev-local role/db `agent_os` created (dev credentials only, never committed).
- **`uv run python scripts/migrate.py` applied all 5 migrations against a real
  PostgreSQL 16.13 for the first time** — previously only ever unit-tested with
  a fake DB. Re-run confirms idempotency ("Database is already up to date").
  Real objects verified: 8 tables, `agent_memories.embedding` is a real
  `vector` column, and `idx_agent_memories_embedding_hnsw` exists.
- Redis 7.0.15 started natively and answered `PING`.
- Backend booted with every `AGENT_OS_*_BACKEND` on `postgres` and the queue on
  `redis`. **`/ready` returned `{"database":"ok","queue":"ok"}` — the first time
  that object has ever been non-empty.** `/health` `backends` map showed
  postgres/postgres/postgres/postgres/postgres/postgres + redis.
- Real business logic exercised through the durable path: created a task
  (persisted), wrote a memory, and ran `POST /api/v1/memory/search`, which
  returned **real hybrid scores from pgvector** (`score` 0.304,
  `semantic_score` 0.345, `lexical_score` 0.0). Orchestration ran end-to-end.
- Live connector probes: **`postgresql` and `redis` are LIVE_VALIDATED** (real
  `SELECT 1` / `PING` through the governed broker, real latency ~40ms / ~1.6ms).
  `n8n`/`openai`/`gemini` correctly returned `503` naming the exact missing env
  var — honest, not faked.
- **Nothing here is production.** This validates the code paths on a local dev
  database; Render still has no `DATABASE_URL`/`REDIS_URL`.

### Browser/visual QA is now portable — and the UI was actually looked at

- `frontend/scripts/screenshot.mjs` **hard-required `REPLIT_PLAYWRIGHT_CHROMIUM_
  EXECUTABLE` and exited immediately without it**, so it was dead everywhere
  except that one Replit sandbox. Rewritten with a portable resolution chain
  (`THYNACT_CHROMIUM_EXECUTABLE` → the Replit var for back-compat →
  `PLAYWRIGHT_BROWSERS_PATH` → playwright-managed → system Chrome → an
  actionable error listing every path tried). It found
  `/opt/pw-browsers/chromium` here with no Replit variable set.
- It now also **fails loudly on page-level horizontal overflow** (exit code 2)
  and can seed the operator session via `THYNACT_SCREENSHOT_API_BASE_URL` /
  `THYNACT_SCREENSHOT_API_KEY`, so authenticated, data-bearing pages can be
  rendered — previously every screenshot could only show a logged-out state.
- **Rendered against a live backend with real data**: Dashboard at 1440×900
  (dark) and 390×844 (dark), Integrations at 1440×1000 (dark), Memory at
  1024×800 (light). No horizontal overflow at any width; console clean.
- Findings: mobile at 390px is **correct** — `1f9ffdc`'s responsive fix is now
  visually confirmed for the first time (stat cards 1-up, Topbar fits on one
  row). Light theme at `8cae377`'s reduced glass alpha is **legible** — the
  long-standing "highest priority single check" in 10_NEXT_STEPS is resolved.
  Integrations showed PostgreSQL/Redis as genuinely **Connected**.
- Two things that *looked* like defects were checked and are **not** bugs (do
  not "fix" them): the account control's offset green dot is a deliberate
  status badge, and the "Anthropic" label is spelled correctly in
  `app/integrations/catalog.py` (a misread of rendered pixels).

### Real defect found and fixed by rendering

- **No favicon existed at all** — no `<link rel="icon">`, no `frontend/public/`.
  Every page load produced a permanent console 404 and a blank browser tab on a
  product whose whole visual direction is "premium". Added
  `frontend/public/favicon.svg` (brand gradient `#8574ff`→`#5bc7ff` + the
  Sparkles glyph matching `BrandMark`) and linked it in `index.html`. Console
  errors on the Dashboard went from 1 to **0**.

### Doc drift corrected

- Backend suite is **230 tests passing**, not the 208 this file claimed.
- Frontend: 48/48 tests, typecheck clean, build clean, lint 0 errors + the same
  2 pre-existing `react-refresh` warnings.
- HEAD was `1b5ccc6`, two commits ahead of the `52c78e1` this file described.
- **Slack, Notion, GitLab and Make already exist in code** (adapters, OAuth
  config entries, Settings fields and tests) while `07_DEFERRED_GOALS.md` still
  described Slack/Notion as speculative. Corrected there.
- Live catalog truth: **28 catalog entries, 13 `implemented`, 2 LIVE_VALIDATED**
  (postgresql, redis). The other 11 implemented connectors are
  CREDENTIAL_REQUIRED or AUTH_REQUIRED, none faked.
- The uploaded Master Guide describes GitHub MCP as `MCP_LIVE_VALIDATED`,
  plus browser/filesystem MCP validation, OIDC sign-in and tenant isolation.
  **This repository contains none of that**: `app/integrations/mcp/` is a
  generic remote-MCP client/store, GitHub is an OAuth adapter, and there is no
  OIDC or tenancy layer. Per the conflict order, the repository wins — treat
  those guide sections as product direction, not present state.

## PRODUCTION STATUS

- **Live frontend:** https://app.thynact.com — HTTP 200. Verified this
  session (after pushing `aad329e`) that Cloudflare Pages auto-deployed
  `origin/main` within ~20s: the served `/assets/index-*.js` hash changed
  from the prior session's `index-CwgnVrCF.js` to `index-Dssa6dw8.js`,
  matching a fresh local `pnpm build` byte-for-byte. Went further than
  the asset-hash check alone this time — fetched the live served CSS
  bundle (`assets/index-Di_zWwI1.css`) directly and grepped it, confirming
  both `Space Grotesk Variable` (the new font) and `accent-violet:#5b4fd6`
  (the new light-theme contrast override, alongside the untouched
  `#8574ff` dark-theme value) are actually present in what's served to
  real users, not just in the local build. The rendering verification
  itself (screenshots, overflow checks) was done against the local dev
  server before pushing — see this session's DONE entry — not re-done
  against the live URL, but the byte-identical asset hash plus this CSS
  spot-check make that a very safe inference. Re-verify the asset-hash
  match the same way after any future push.
- **Live API:** `https://api.thynact.com/health` still returns `200`
  with `"status":"ok"` — reconfirmed this session; unaffected since no
  backend code changed.
- **Live API:** https://api.thynact.com — `/health` returns
  `{"status":"ok","service":"THYNACT","environment":"development","llm_provider":"mock",...}`
  (HTTP 200). `/ready` returns `{"status":"ready","checks":{}}` (HTTP 200).
  `GET /api/v1/integrations` (public, no key needed) was fetched live this
  session and confirmed to already reflect this session's catalog changes
  (openai/anthropic/cloudflare/render/github all `implemented:true`,
  github's `requires` lists `GITHUB_OAUTH_CLIENT_ID`/`_SECRET`) — Render
  auto-deployed `origin/main` within the session, before this file was
  even updated. The empty `/ready` `checks` object is expected/correct: it
  means every backend (memory/queue) is currently set to `memory`, so
  there's nothing to health-check yet (see PERSISTENCE below).
- `environment: "development"` in the live `/health` response — the Render
  service does not have `AGENT_OS_APP_ENV`/environment override set to
  `production`. Cosmetic, not a functional blocker. UNVERIFIED whether this
  is intentional.
- Auth is live and enforced on protected routes, confirmed fresh this
  session: unauthenticated `GET /api/v1/tools` returns `401
  {"detail":"Unauthorized"}` (not `503`), which means `AGENT_OS_API_KEY`
  **is** configured on the Render production service. **Correction to a
  stale claim in an earlier version of this file:** `GET
  /api/v1/integrations` (the connector catalog) is deliberately public
  and returns `200` with no auth header at all — that's intentional
  (`public_router` in `app/api/phase9.py`, added in an earlier session so
  the Integration Hub renders for any visitor) and was reconfirmed live
  this session, not a regression. This session does not have the real
  `AGENT_OS_API_KEY` value and cannot exercise *protected* endpoints
  against production directly — see "NEEDS CREDENTIALS" and
  10_NEXT_STEPS.md.

## Environment note

Mid-session, `git push origin main` failed once with "Invalid username or
token" from the Replit-managed git askpass helper (`replit-git-askpass`),
even though `gh auth status` showed a valid, active GitHub CLI login with
`repo` scope. Fixed by running `gh auth setup-git` (routes git's credential
resolution through the already-authenticated `gh` CLI) and retrying — no
secrets were exposed, nothing destructive was done. If a future session
hits the same "Invalid username or token" push error, try this first
before assuming a deeper auth problem. **Confirmed recurring**: this exact
same failure + fix happened again at the start of the very next session
(this one) — the git credential wiring does not persist across sessions
in this environment, so expect to run `gh auth setup-git` once per fresh
session, every time, rather than treating it as a one-off fix.

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
- **Integration Hub UX overhaul (this session).** Replaced the old
  alarm-styled "Not configured. Set `X` on the backend to enable this
  connector." box with neutral requires-setup copy/styling
  (`ConnectorDrawer.tsx`), matching CLAUDE.md's setup-state-is-not-an-
  error rule. New reusable components: `ConnectorCard`, `ConnectorDrawer`,
  `AddMcpServerDialog`, `AuthRequiredBanner`, `connectorIcons.ts`, and
  `lib/integration-hub.ts` (merges the static catalog with user-added MCP
  servers into one `UnifiedConnector` list — Currently
  integrated/Popular/All sections, search, and category/type filter
  chips). Fixed a real crash: `mcpServerToConnector()` threw
  `Cannot read properties of undefined (reading 'tools')` whenever an MCP
  server API response omitted `capabilities` — now defensively defaults to
  empty capability lists (`ConnectorDrawer.tsx` had the same unguarded
  access, fixed too).
- **App-wide "missing operator key" UX fix (this session, real bug).**
  `ErrorState` (used by 12 pages — Dashboard, Tasks, Workflows, Memory,
  Tools, Runtime, Audit, etc.) rendered a 401/503 from any protected
  endpoint with the same alarm-red "Something went wrong" full panel as a
  genuine failure. Since most API calls require the operator key and a
  fresh browser tab has none set, **most pages showed a giant red error
  box on first load** — exactly the "giant Unauthorized panel" CLAUDE.md
  says to avoid. `ErrorState` now special-cases `ApiError.isUnauthorized`
  (401/503) into a compact neutral banner with a "Configure API key" link
  to Settings, reusing the treatment already built for the Integrations
  page. `States.test.tsx` updated to assert the neutral treatment and that
  the old alarm copy is gone.
- **Fixed a real 404 bug: Test connection on Gemini/PostgreSQL/Redis.**
  These three have had `implemented=True` catalog entries with live status
  computed since an earlier session, and their "Test connection" button
  was enabled in the UI — but `IntegrationProvider`/`list_providers()`
  only ever contained `n8n`, so clicking Test on any of the other three
  404'd. Fixed by giving each a real adapter (`GeminiAdapter` — lists
  models via a free read call; `PostgresAdapter` — `SELECT 1` against
  `DATABASE_URL` independent of whether Postgres is the active backend;
  `RedisAdapter` — `PING` against `REDIS_URL` independent of whether Redis
  is the active queue) and registering all three in
  `app/integrations/factory.py`. Live status resolution in
  `app/api/phase9.py` was also refactored into one shared
  `_status_store_backed_status()` helper so `connected`/`error` now
  reflects the actual last test result via `status_store`, not just static
  settings — previously Postgres/Redis status literally ignored
  `status_store` even though the (broken) Test button wrote to it.
- **New real adapters: OpenAI, Anthropic, Cloudflare, Render (this
  session).** Each does a genuine, free, read-only verification call
  (`GET /v1/models` for OpenAI/Anthropic/Gemini, Cloudflare's dedicated
  `/user/tokens/verify`, Render's `/v1/owners`) — never a fake success,
  never an expensive/destructive call. All four flipped from
  `CATALOG_ONLY` to `READY_FOR_AUTH` (`implemented=True`,
  `requires=["<PROVIDER>_API_KEY"]` / `CLOUDFLARE_API_TOKEN` /
  `RENDER_API_KEY`). `execute()` is intentionally "not supported" for all
  of these — they're identity/read-only connectors, not triggered
  webhooks, and catalog `capabilities` were corrected to match (e.g.
  OpenAI now lists "Verify API key"/"List models", not "Chat completion",
  which isn't wired to anything).
- **Generic OAuth2 foundation + GitHub reference implementation (this
  session).** New `app/integrations/oauth/` package: provider config
  (authorize/token URLs, scope, env var names), a single-use/TTL'd CSRF
  state store, a redacted connection store (access tokens never leave
  process memory or appear in any API response), and
  `build_authorize_url()`/`exchange_code()`. New routes:
  `GET/POST /api/v1/integrations/oauth/{provider}/authorize` (operator-
  gated), `GET .../callback` (necessarily public — the provider's browser
  redirect can't carry an `X-API-Key`; protected by the state token
  instead), `DELETE /api/v1/integrations/oauth/{provider}` (disconnect).
  GitHub is wired end-to-end: catalog flipped to `implemented=True`,
  `GitHubOAuthAdapter.test_connection()` verifies a stored token via
  `GET /user`, live status is `needs_setup` (no client id/secret) →
  `configured` (creds present, not yet authorized) → `connected` (token
  obtained). Frontend: `ConnectorDrawer` shows "Authorize" (redirects to
  the provider) for unconnected OAuth connectors and "Disconnect" once
  connected; `Integrations.tsx` shows a toast and cleans the URL when the
  browser returns from the callback redirect (`?oauth=connected&provider=`
  / `?oauth=error&...`). Adding the next OAuth provider (Slack, Notion,
  ...) is a config entry in `oauth/config.py` plus two Settings fields —
  see 10_NEXT_STEPS.md.
- **Backend test suite: 208/208 passing** (`python -m pytest tests/ -q`) —
  up from 137, all net-new tests from this session's adapter/OAuth/UX work
  (none removed; the two stale n8n-shaped assertions in
  `Integrations.test.tsx` and `test_integrations_catalog.py`'s
  now-implemented `github` example were updated in place, not skipped).
- **Frontend: 29/29 tests passing** (`npm run test`) — up from 25.
  **Typecheck clean** (`npm run typecheck`), **lint clean** — 0 errors, 2
  pre-existing warnings unrelated to this session's changes (`Toast.tsx`,
  `theme.tsx`, `react-refresh/only-export-components`), **production
  build clean** (`npm run build`).
- **Environment note (this session):** the frontend was built/tested with
  `npm` (a `package-lock.json` exists alongside `pnpm-lock.yaml`), not
  `pnpm` as 00_START_HERE.md's deployment section describes for
  Cloudflare's build step. Both installed the same dependency versions
  (no `package.json` changes this session, so no lockfile drift) and the
  live asset-hash check above confirms Cloudflare's actual `pnpm`-based
  build still matches — but a future session should prefer `pnpm` if
  available, to stay consistent with what production actually builds
  with.

- **THYNACT glass/motion design system (this session, HEAD `70cf378`).**
  Built the systemic foundation requested by the "premium UI/motion
  upgrade" brief instead of redesigning every page by hand — see
  00_START_HERE.md's new "Frontend design system" section for the full
  primitive list (`GlassSurface`, glass-ambient/soft/panel/focus + border-
  hairline CSS, `AmbientBackground`, `lib/motion.ts`, `ScrollReveal`/
  `StaggerGroup`/`StaggerItem`, `AccountPopover`). Because `Card`/
  `MetricCard` alone are used across 14+ pages, converting those two
  components to the glass system cascaded the "no more page → bordered-
  card → bordered-card" fix app-wide without touching every page
  individually; `Drawer`/`Dialog`/`CommandPalette`/`AppShell`/`Sidebar`/
  `Topbar` and the `AgentCard`/`ConnectorCard`/`StepNode` flagship
  components were each additionally updated by hand. Dashboard got the
  full bespoke pass the brief called out specifically: the "Dashboard /
  Live status of..." heading block is gone, the bordered hero rectangle is
  gone (replaced by a borderless ambient hero — staggered text entrance,
  a soft floating glow, a one-shot animated scan line), and every section
  below it now enters via `ScrollReveal`/`StaggerGroup` (`whileInView`,
  fires once, no scroll-jacking — native scroll untouched). New circular
  `AccountPopover` beside the sidebar hamburger surfaces the one real
  identity concept THYNACT has (the operator's local API-key session) —
  configured/not-configured state, API base URL, a "Clear session" action
  wired to the existing `resetApiConfig()`; deliberately does not invent
  account fields the backend doesn't have. Sidebar's active-nav highlight
  is now an animated `layoutId` pill. All motion respects
  `prefers-reduced-motion` (`AmbientBackground`'s parallax/particles check
  `useReducedMotion` explicitly since they're JS-driven, not CSS
  animations that the existing global reduced-motion override would
  catch). Added a no-op `IntersectionObserver` mock to
  `frontend/src/test/setup.ts` (jsdom has none; Framer Motion's
  `whileInView` throws without one — this was a real crash caught by
  `App.test.tsx`, not a pre-existing gap). **Not done in this pass** (see
  PARTIAL below and 07_DEFERRED_GOALS.md): bespoke cinematic treatments
  for Orchestration/Autonomous/Memory/Workflows beyond what the shared
  glass/motion cascade already gives them, and all interactive/visual QA
  (browser tooling still unavailable to this session — see BLOCKED).
  Verified via `pnpm typecheck` / `pnpm lint` / `pnpm test` (43/43,
  including a new IntersectionObserver-dependent path) / `pnpm build` —
  all clean.

- **Account popover bug fix + heartbeat line + gold/red ambient background
  (this session, HEAD `4eb018a`).** A follow-up premium-UI pass on top of
  the prior session's glass/motion foundation (HEAD `70cf378`):
  - **Real bug fixed**: `AccountPopover` (the circular profile control
    beside the sidebar hamburger, added last session) was positioned
    `absolute right-0` — correct for a control near the *right* edge of a
    toolbar, but this control sits near the *left* edge, so its 256px-wide
    panel expanded off-screen to the left and effectively nothing usable
    appeared when clicked. This is almost certainly the "login/account
    option is not opening properly" issue reported. Fixed to `left-0` with
    a `max-w-[calc(100vw-2rem)]` viewport safety net; also switched the
    outside-click listener from `mousedown` to `pointerdown` for more
    reliable touch behavior and added `aria-haspopup`/`type="button"`.
  - **API heartbeat line**: `components/ui/HeartbeatLine.tsx` replaces the
    blinking-dot status indicator with an ECG-style trace (online =
    looping waveform via SVG SMIL `animateTransform`; connecting = same
    waveform static + breathing opacity; offline = flat straight line, no
    motion). Wired into `HealthIndicator` (top-right) and Dashboard's API
    status metric (new optional `MetricCard` `graphic` slot). Explicitly
    checks `useReducedMotion` since SMIL isn't covered by the CSS
    `prefers-reduced-motion` override used everywhere else.
  - **Black/gold/deep-red ambient background**: new `--color-ambient-wine`
    token (index.css) kept deliberately separate from `--color-accent-red`
    (status semantics untouched); a faint radial-gradient `body`
    background in dark mode; `AmbientBackground`'s mesh glows/grid/data
    points and the Dashboard hero's glow/scan-line retinted from
    violet/blue to gold/wine. Interactive accents (buttons, links, nav
    active state, the BrandMark wordmark gradient) were deliberately left
    violet — this was scoped to the ambient/background system per the
    brief's explicit "background" section, not a full brand recolor.
  - **Locked-state polish**: Dashboard's audit `AuthRequiredState` and the
    Integrations `AuthRequiredBanner` now use a `Lock` icon + `glass-soft`
    surface instead of a flat `KeyRound` strip (copy also now says the
    catalog stays browsable — it never did block the page, but said so
    less clearly before); `ErrorState`/`EmptyState` softened from solid
    borders to glass + hairline while staying visually distinct for
    genuine errors.
  - **Integrations honesty/polish**: added the real `google` catalog
    category as a selectable filter chip (it existed in the `ConnectorCategory`
    type and satisfies real connectors like Google Calendar/Drive, but had
    no chip); did **not** add a fabricated "Storage/Infra" section since
    no such backend category exists — see 00_START_HERE.md's category
    list before inventing one. Filter chips/dividers softened to
    hairline+glass; "All integrations" wrapped in `ScrollReveal`. The
    Currently-integrated/Ready-to-connect/Popular/All structure and the
    honest CONNECTED/READY TO CONNECT/COMING SOON state machine
    (`lib/integration-hub.ts`) already existed from prior sessions and
    were not changed.
  - **Whole-app border pass**: `border-surface` → `border-hairline` (plus
    `glass-ambient` on nested sub-panels) across Audit, Runtime,
    SystemHealth, Memory, Tasks, WorkflowRuns, Settings, and
    `ConnectorDrawer`. Remaining `border-surface` usages are legitimate
    interactive-affordance chrome (`Button`/`Input`/`Badge`/`Tabs`/
    `Toast`/`Skeleton`) — intentionally left alone, see
    00_START_HERE.md's design-system note.
  - Verified via `pnpm typecheck`/`pnpm lint`/`pnpm test` (43/43)/`pnpm
    build` — all clean. No backend code touched this session.

- **Cream/bronze/deep-navy background palette + final border sweep (this
  session, HEAD `8a9dd81`).** A third consecutive premium-UI pass; a new,
  more specific reference palette was given (`#F5E9DD` cream / `#A67C52`
  bronze / `#122D70` deep navy over near-black), which **supersedes** the
  prior session's gold/deep-red ambient direction. Replaced
  `--color-ambient-wine` with `--color-ambient-cream`/`-bronze`/`-navy`
  (index.css); reworked `body`'s dark-mode gradient and
  `AmbientBackground`'s mesh glows/data points and Dashboard's hero
  glow/scan-line to match. `--color-accent-*` (interactive/status tokens)
  were left untouched, same reasoning as before — this is scoped to
  ambient decoration, not a brand recolor. Also finished the whole-app
  hard-border sweep started two sessions ago: `Skeleton`'s loading
  placeholder, `JSONViewer`, `MemoryGraph`'s hover panel,
  `OrchestrationPipeline`/`Timeline`'s pending-state ring color —
  `border-surface` → `border-hairline` (+ `glass-*` where it's a
  standalone panel). What's left using `border-surface`/
  `bg-surface-raised` is now only legitimate interactive-affordance
  chrome (`Button`/`Input`/`Badge`/`Tabs`/`Toast`) and the React Flow
  `MiniMap` (needs an opaque background to stay legible over the canvas)
  — there is no more "boxy card" surface left to soften; a future request
  to "remove more hard borders" should start from that premise, not
  re-sweep from scratch. `MetricCard` also got more padding, an
  uppercase-tracked label, and larger/tighter value type for stronger
  hierarchy (no data changes).
  - **Everything else this new request asked for** — the old Dashboard
    heading block removed, the borderless hero, the account-icon bug fix,
    the waveform/heartbeat API status language (green online / amber
    connecting / red straight-line offline), the Integrations honest
    states and Search/Popular/Currently-integrated/Ready-to-connect
    structure — **was already implemented and verified in the
    immediately preceding two sessions** (HEAD `70cf378` then `4eb018a`)
    and was re-confirmed still present, not re-built. See those entries
    above for implementation detail; nothing new was needed for them this
    session beyond the palette/border items above.
  - Verified via `pnpm typecheck`/`pnpm lint`/`pnpm test` (43/43)/`pnpm
    build` — all clean. No backend code touched.

- **Invisible-background root-cause fix + portal `AccountPopover` +
  multi-cycle `HeartbeatLine` (HEAD `776dd63`, committed but not yet
  pushed at the start of this session — see push status above/below).**
  The actual root cause, finally found: `AppShell`'s root `div` carried
  `bg-surface-canvas`, a fully **opaque** background-color, painted
  directly on top of `body`. Every prior session's ambient-gradient/
  cream-bronze-navy work (HEAD `70cf378` through `8a9dd81`) was rendering
  onto a layer nothing could ever see — this is why three consecutive
  sessions kept re-tuning gradient opacity by reasoning alone and it
  never looked right. `bg-surface-canvas` removed from `AppShell`'s root;
  `body`'s gradient now actually reaches the screen. Also: dropped a
  fourth "vignette" radial layer from `body`'s dark-mode gradient that was
  cancelling out most of the cream/bronze/navy color underneath it,
  roughly doubled the remaining three layers' color-mix intensity, and
  moved the navy blob on-screen (was 98%/102%, now 88%/82%). Reduced
  dark-mode glass alpha to compensate now that the gradient is actually
  visible (`.dark .glass-ambient` 0.28→0.2, `.dark .glass-soft` 0.46→0.34,
  `.dark .glass-panel` 0.62→0.5 in `index.css`; `.dark .glass-focus`
  (0.88), used for dialogs/drawers, deliberately left alone for
  legibility). Separately:
  `AccountPopover` rewritten to render through a portal to `document.body`
  (matching `Drawer`/`Dialog`/`CommandPalette`, the pattern it should have
  followed originally) with position computed from the trigger's real
  `getBoundingClientRect()`, clamped on-screen, recomputed on resize —
  below the `sm` breakpoint it renders as a full-width bottom sheet
  instead of a floating popover. This replaces the `right-0`/`left-0`
  coordinate-guessing fix from two sessions ago with a fix to the actual
  positioning strategy. `HeartbeatLine` fixed to derive its SVG `viewBox`
  width from the requested aspect ratio and repeat the correct number of
  waveform cycles to fill it, instead of letterboxing one stretched cycle
  in empty space on wide instances (e.g. Dashboard's). `AuthRequiredState`
  copy changed to "Operator authentication required" / "Authenticate".
  New `HeartbeatLine.test.tsx` (5 new tests: multi-cycle online rendering,
  more cycles on a wider instance, static offline line, static amber
  connecting state, reduced-motion behavior).
  - **Per the commit message**, this was the first session with headless
    Chromium available in a scratch environment, and the above was found
    and confirmed by actually rendering the app and looking, not by code
    review alone — at desktop/iPad-portrait/mobile, confirming the
    gradient visible, cards reading as glass against it, the account
    popover/sheet on-screen at every size, and the offline heartbeat as a
    flat red line. **This session found no repository record of how that
    browser tooling was obtained** — nothing in `frontend/package.json`,
    no Playwright/Puppeteer dependency, no committed script — so it was
    evidently ephemeral to that prior sandbox and should not be assumed
    available in a future session by default; see BLOCKED below.
  - Verified via `pnpm typecheck`/`pnpm lint` (0 errors, 2 pre-existing
    warnings)/`pnpm test` (48/48, 5 new)/`pnpm build` — all clean, per the
    commit message. Not independently re-run this session since no code
    has changed since that commit. No backend code touched.

- **Glass translucency retune + glass form fields + light-mode gradient
  (this session, HEAD `8cae377`).** A new, more specific brief gave a
  concrete alpha target (~0.04-0.16 for cards/sections) and named exact
  surfaces that must not look opaque, including forms/inputs and
  dropdowns. This session's audit found the central glass system
  (`GlassSurface`, `Card`/`MetricCard`, `Sidebar`/`Topbar`, `Dialog`/
  `Drawer`/`CommandPalette`/`AccountPopover`) was already architecturally
  centralized exactly as the brief asked — no page had its own bespoke
  opaque surface — so this was a one-file retune (`index.css`), not a
  page-by-page rewrite:
  - `.glass-ambient`/`.glass-soft`/`.glass-panel` alpha cut roughly 3-5x
    in both themes (dark: 0.2/0.34/0.5 -> 0.06/0.1/0.15; light: 0.3/0.55/
    0.72 -> 0.08/0.12/0.16) with blur bumped slightly (6/14/20px ->
    9/16/22px) to compensate for legibility at the lower alpha.
  - `.glass-focus` (dialogs/drawers/popovers/dropdowns — the tier that
    overlays real page content, not just the ambient background)
    deliberately kept as the most opaque tier per the brief's "slightly
    stronger modal/overlay glass," but still cut substantially (dark
    0.88->0.4, light 0.92->0.55) — no longer near-solid like before.
  - New `.glass-field` tier (dark 0.28 / light 0.22 alpha, 10px blur) for
    `Input`/`Textarea`/`Select` (`components/ui/Input.tsx`), which
    previously used fully opaque `bg-surface-canvas`. This is a
    **reversal** of an earlier session's explicit call that Input was
    legitimate opaque "interactive chrome" alongside Button/Badge/Tabs/
    Toast — the new brief specifically named forms/inputs as a surface
    that must read as glass, so that precedent no longer applies to
    Input specifically. Button/Badge/Tabs/Toast/the React Flow `MiniMap`
    were left as-is (small interactive affordances or, for MiniMap, a
    documented need for opaque contrast over the canvas) since the brief
    didn't name them and changing them wasn't asked for.
  - Light mode previously had **no** ambient gradient at all — only
    `.dark body` did (`AmbientBackground`'s grid/glow/points layer runs
    in both themes, but the base gradient wash was dark-only). Added a
    light-mode gradient using the same `--color-ambient-cream/-bronze/
    -navy` tokens (not new colors — reuses the existing palette per "no
    random gradients") at much lower color-mix intensity (7-55% vs
    dark's 16-48%) since a light background goes muddy far faster than
    near-black.
  - Verified via `pnpm typecheck`/`pnpm lint` (0 errors, 2 pre-existing
    warnings)/`pnpm test` (48/48, no test changes needed)/`pnpm build` —
    all clean. **Not visually verified in a real browser** — no browser
    tooling available in this session either (Claude-in-Chrome tools were
    not present); the alpha/blur values above were chosen by reasoning
    about contrast, not by rendering and looking. This is the single
    highest-priority follow-up — see BLOCKED below and 10_NEXT_STEPS.md.
  - Backend untouched.

- **Mobile/small-tablet responsive layout fix (this session, HEAD
  `1f9ffdc`), source-level audit only — see BLOCKED below.** The operator
  checked the live site on an actual mobile device after the glass
  retune shipped and reported it "still behaving like a squeezed desktop
  layout," with a concrete list of symptoms (Dashboard stat cards stuck
  at 2 narrow columns, cramped Topbar, poor text wrapping, inconsistent
  card sizing). Audited the responsive architecture first (Tailwind v4
  defaults — `sm`=640/`md`=768/`lg`=1024px, no custom breakpoints
  configured) rather than patching screens individually. Root causes
  found:
  - Dashboard's 4 stat cards used `grid-cols-2` as an **unconditional
    base class** (`pages/Dashboard.tsx`), so they rendered 2-up at every
    width below 1024px, including phones — this was the actual cause of
    both the "2-column squeeze" complaint and the "This session" card's
    hint text ("Tasks, runs & executions started here") wrapping badly:
    the card was simply too narrow, there was no separate text-wrapping
    bug to fix. Now `grid-cols-1` (base) → `sm:grid-cols-2` (640px+) →
    `lg:grid-cols-4` (1024px+, unchanged).
  - The same unconditional `grid-cols-2` pattern existed in six other
    places for paired form fields / metadata `dl`s:
    `StepEditorDialog.tsx` (x2), `Runtime.tsx` (Execute form + execution
    detail `dl`), `Tasks.tsx` (New-task form + task-card `dl`),
    `ConnectorCard.tsx` (last-checked `dl`) — all switched to
    `grid-cols-1 sm:grid-cols-2` so they stack below 640px instead of
    cramming two fields into ~150px each on a phone.
  - `Topbar.tsx` was genuinely overcrowded: hamburger + `AccountPopover`
    + a `flex-1` search bar + (API-key badge + `HealthIndicator` with a
    waveform *and* text label + theme toggle + settings) all competing
    for one 320-375px row. Fixed by making the search control collapse
    to an icon-only square button below `sm` (it was previously an empty
    stretched pill — the label was already hidden but the container
    still claimed `flex-1` space) and `HealthIndicator.tsx` dropping its
    text label below `sm` (keeps the colored heartbeat waveform +
    tooltip, which already conveys state). Header padding/gaps tightened
    on mobile (`px-3`/`gap-1.5`) vs desktop (`px-4`/`gap-3`, unchanged).
    Hamburger touch target `p-1.5`→`p-2`; `AccountPopover`'s trigger
    `h-8`→`h-9` to match the other 36px icon buttons in the header.
  - `Workflows.tsx`'s "Step graph" toolbar (3 buttons — Add step/Delete
    selected/Run workflow — with no `flex-wrap`) could overflow its row
    on narrow screens; added `flex-wrap`. `WorkflowRuns.tsx`'s
    resume-step rows (a fixed `w-32` label next to an `Input` in a flex
    row) now stack label-above-input below `sm`. `CommandPalette.tsx`'s
    outer overlay had no horizontal padding at all, so the palette sat
    flush against both screen edges on mobile; added `px-4`.
  - Two Dashboard grids that already relied on bare `grid`'s default
    single-column-stacking behavior (no explicit `grid-cols-N`) got an
    explicit `grid-cols-1` base added anyway, for clarity/consistency —
    not because they were broken.
  - **Audited and found already correct, deliberately not touched**:
    `Sidebar` (proper off-canvas drawer below `lg`, `-translate-x-full`
    when closed, fixed-positioned so it can't contribute to page width);
    `Dialog` (`w-full` + `max-w-*` inside a `p-4` flex-centered overlay —
    this correctly caps at `100vw - 32px`, verified by reasoning through
    how percentage widths resolve in a flex-centered container, not
    guessed); `Drawer` (`w-full max-w-md` with no container padding —
    correctly fills exactly `100vw` on mobile, the standard full-screen-
    sheet pattern, not a bug); `AccountPopover`'s existing popover/sheet
    split (already switches to a full-width bottom sheet below 640px
    with a viewport-clamped floating popover above it — built in the
    `776dd63` session, still correct); `PageHeader` (already
    `flex-col` → `sm:flex-row`, used on every page); `Audit.tsx`'s and
    `WorkflowRuns.tsx`'s tables (already wrapped in `overflow-x-auto`
    with `min-w-[...]` on the `<table>` itself — the correct
    "intentional internal scroll" pattern the brief asked to preserve,
    left as-is); every other bare `grid ... sm:grid-cols-N` /
    `lg:grid-cols-N` pattern app-wide (roughly two dozen instances across
    `Approvals`/`Autonomous`/`Agents`/`Tools`/`Memory`/`Integrations`/
    `SystemHealth`/etc.) — CSS grid's documented default behavior
    (`grid-template-columns: none`) is to stack items in a single column
    below the first breakpoint that defines columns, so these were
    already correct and did not need a `grid-cols-1` base added.
  - Verified via `pnpm typecheck`/`pnpm lint` (0 errors, 2 pre-existing
    warnings)/`pnpm test` (48/48, no test changes needed)/`pnpm build` —
    all clean. **Explicitly NOT visually verified in a real browser** —
    Claude-in-Chrome tools were checked for (via tool search) at the
    start of this task and are still not available. Every finding and
    fix above comes from reading component source and applying Tailwind
    v4's documented breakpoint/grid semantics, never from seeing the
    rendered UI. The operator's original mobile screenshot was referenced
    in their instructions but was not actually attached/visible to this
    session, so this fix was also not checked against that specific
    image. **Do not describe mobile as "fixed" or "verified" beyond
    this source-level audit until it has actually been rendered and
    looked at** — see BLOCKED below.
  - Backend untouched. No API/auth/route changes.

- **Dashboard hero cleanup, equal metric cards, light-theme contrast,
  Space Grotesk (this session, HEAD `aad329e`) — first session with
  real committed browser QA, see BLOCKED-RESOLVED above.** A focused UI
  refinement request with 5 parts, all done and actually rendered
  (not just reasoned about) at 320/360/390/430/640/768/1024px in both
  themes via the new `pnpm screenshot` tooling:
  - **Hero paragraph removed.** `Dashboard.tsx`'s long descriptive
    line ("Built to Think. Powered to Act. From intelligence to
    execution...") is gone; the short tagline "Built to Think.
    Powered to Act." remains because it was already rendered
    separately by `BrandMark`'s `variant="full"` (the removed line was
    a second, redundant copy of the same tagline plus extra text).
    The wrapping `flex flex-col gap-3` collapsed to a plain block since
    it now has one child, so no dead vertical space was left — visually
    confirmed the metric cards now sit directly under the wordmark.
  - **Four dashboard metric cards now equal height.** `MetricCard.tsx`'s
    root now has `flex h-full flex-col`, and each `StaggerItem` wrapping
    one on the Dashboard grid got `className="h-full"` — CSS grid's
    default `align-items: stretch` already gives every grid item the
    tallest row's height, this just makes the two nested divs actually
    fill it. No arbitrary per-card pixel heights. Confirmed visually:
    API Status/Tools Available/Audit Events/This Session render as one
    consistent card system regardless of hint/graphic content; shorter
    cards get blank space at the bottom rather than shrinking, which
    is the intended tradeoff (no fabricated filler content).
  - **Sidebar light-theme text contrast fixed — real defect, not just
    a token-value tweak.** `Sidebar.tsx`'s inactive nav item labels
    (Dashboard/Tasks/Orchestrate/.../Settings) were using
    `text-content-secondary` (`#4b4f5a`), the app's *secondary* text
    tier, for what is semantically primary navigation copy — changed
    to `text-content-primary` (`#14161c`). Both tokens technically
    passed WCAG AA against white in isolation, but the secondary tier
    read visibly paler than the rest of the app's primary text, which
    is what the operator's annotated screenshot flagged. Section group
    headers (OVERVIEW/EXECUTION/etc.) intentionally kept softer via
    `text-content-muted`.
  - **`--text-content-muted` darkened for light theme** (`#767a86` →
    `#5b6270` in `index.css`) — the old value computed to ~4.3:1
    contrast against white, under the 4.5:1 AA threshold for normal-
    size text; used app-wide for hints/timestamps/uppercase labels, so
    this is one central fix rather than a per-page sweep. Dark-theme
    muted (`#8d919d`) untouched.
  - **Light-theme-only `--color-accent-violet` retune** (`index.css`,
    inside the existing `html:not(.dark)` block): `#8574ff` (~3.5:1
    against white — under AA for both text and white-on-violet button
    labels) → `#5b4fd6` (~5.9:1), still clearly violet/on-brand. This
    is a single CSS-custom-property override, unlayered so it beats
    Tailwind v4's `@theme`-generated (layered) declaration regardless
    of source order/specificity — every existing `text-accent-violet`/
    `bg-accent-violet`/`border-accent-violet` usage across the app
    (buttons, sidebar active state, links, badges) picks it up
    automatically in light mode only. Dark mode's `#8574ff` is
    completely untouched (no `.dark` override needed — it was never
    overridden, only light mode was). Visually confirmed: sidebar
    active-item text, the Settings "Save configuration" button
    (white-on-violet), and the Settings "Light" appearance toggle
    (violet-on-white) all read clearly now in both the light Dashboard
    and Settings screenshots.
  - **Typography switched to Space Grotesk app-wide, one token.**
    Installed `@fontsource-variable/space-grotesk` (self-hosted, no
    external CDN — avoids the FOUC/CSP/offline-dev risk of a Google
    Fonts `<link>`) as a real `dependency`; `index.css` gained
    `@import "@fontsource-variable/space-grotesk";` and
    `--font-sans: "Space Grotesk Variable", "Inter", ui-sans-serif,
    system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI",
    sans-serif;` — one line, no per-component font-family edits
    anywhere. The variable font's declared weight range is 300–700, so
    the app's existing `font-medium`/`font-semibold`/`font-bold`
    utility classes (400/500/600/700) all render correctly without any
    additional weight-specific imports. Confirmed via a fresh `pnpm
    build` that all 3 latin/latin-ext/vietnamese `.woff2` subsets are
    emitted to `dist/assets/` with `font-display: swap`, and that the
    built CSS's `--font-sans` and `@font-face` rules are present and
    correct (not just present in dev). Visually confirmed rendering
    (distinctive Space Grotesk letterforms visible in the wordmark, nav
    labels, numerals) with no clipped/wrapped/overflowing labels found
    in the Dashboard, Tools, or Settings screenshots at any tested
    width, and no horizontal page overflow at any of the 7 target
    breakpoints (`document.documentElement.scrollWidth ===
    clientWidth` checked programmatically, not just visually, at all
    of 320/360/390/430/640/768/1024px).
  - **Dark theme reconfirmed unchanged**: screenshot comparison at
    1440×900 shows glass translucency, ambient background particles,
    card equal-height fix, and the (untouched) `#8574ff` violet all
    still correct.
  - **New reusable QA tooling** (see BLOCKED-RESOLVED above for the
    technical why): `frontend/scripts/screenshot.mjs` +
    `pnpm screenshot`, `playwright` added as a real `devDependency`.
  - Verified via `pnpm typecheck` (clean) / `pnpm lint` (0 errors, the
    same 2 pre-existing warnings) / `pnpm test` (48/48, no test changes
    needed — no test asserted the old hero paragraph or old colors) /
    `pnpm build` (clean, `.woff2`/`@font-face`/`--font-sans` confirmed
    in the built CSS) / actual rendering via the new `pnpm screenshot`
    tooling as detailed above. Backend untouched — frontend-only
    presentation change, no API/auth/route/business-logic edits.
    **Not yet re-verified against the live `app.thynact.com` deploy**
    at the time this entry was written — see PRODUCTION STATUS for
    whether that follow-up check happened this session.

## PARTIAL

- **Workflow builder** is functional and has 3/4 flagship features (node
  toolbar, validation highlighting, execution-pulse edges — see DONE
  above); only the context side panel (editing is still a modal dialog,
  deliberately) is not done.
- **Premium motion pass**, prior sessions: Dashboard (brand moment), API
  heartbeat, Workflows canvas, Orchestrate (pipeline visualization), Memory
  (match-score bar + relationship graph), Runtime (circuit-breaker/rate-
  limit gauges), System Health (persistence map), Audit (timeline view),
  Autonomous (parallelism badge + grid).
- **Glass/motion design-system pass (this session)**: every page that uses
  `Card`/`MetricCard` (14+ pages, effectively the whole product) inherited
  the glass-panel/glass-soft treatment and border-hairline separators for
  free; `Dashboard` additionally got the full bespoke pass the brief
  required by name (hero/heading rework — see DONE above).
  `AgentCard`/`ConnectorCard`/`StepNode` were hand-touched too. **What
  this pass deliberately did NOT do**: bespoke cinematic upgrades beyond
  the shared cascade for Orchestration (animated data-flow/execution
  particles), Autonomous (evolving computation-graph visualization),
  Memory (spatial/semantic-similarity graph movement), Workflows (edge
  pulse/glow refinement, minimap polish, floating config drawer instead of
  the modal editor), Agents (computational-entity treatment beyond the
  glass card), Approvals, Tools, Runtime (execution timeline), Audit
  (correlation-ID copy). These remain fair game for a focused follow-up
  session — see 07_DEFERRED_GOALS.md and 10_NEXT_STEPS.md.
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

## BLOCKED (historical — RESOLVED this session, HEAD `aad329e`, see DONE below)

**Update, HEAD `aad329e`:** the "no browser tooling" blocker below is now
resolved and, unlike `776dd63`'s one-off ephemeral setup, **committed** so
it survives to future sessions: `frontend/scripts/screenshot.mjs` (run via
`pnpm screenshot <url> <outPath> [theme] [width] [height]`) launches
Playwright's `chromium` with `executablePath` pointed at
`$REPLIT_PLAYWRIGHT_CHROMIUM_EXECUTABLE` — the Replit-provided nix-linked
Chromium binary. This was necessary because playwright's own downloaded
browser (`~/.cache/ms-playwright`) fails to launch in this container
(`error while loading shared libraries: libglib-2.0.so.0`, a nix/glibc
mismatch, not a playwright bug) — `npx playwright screenshot` and any
plain `chromium.launch()` without an explicit `executablePath` will hit
this and fail. `playwright` itself is a committed `devDependency` (not a
prod dependency — dev-only, doesn't affect the deployed bundle). Rest of
this section describes the state before this fix, kept for history —
treat "browser tooling unavailable" as no longer true going forward,
re-verify `REPLIT_PLAYWRIGHT_CHROMIUM_EXECUTABLE` is still set if a future
session finds `scripts/screenshot.mjs` failing.

- **No interactive browser tooling connected in this session.**
  Claude-in-Chrome was checked for (via tool search) twice this session —
  once before the glass-alpha work and again before the mobile-responsive
  work — and was not available either time. All frontend verification
  this session was via `vitest` (jsdom), `tsc`, `eslint`, and `vite
  build` — including for both the `8cae377` glass-alpha retune (real
  visual risk: lower alpha could hurt text contrast on some surfaces)
  and the `1f9ffdc` mobile-responsive fix (the operator explicitly
  reported a live-device mobile screenshot as source of truth for this
  work, but that image was not actually attached to/visible in this
  session — the fix is a source-level Tailwind-breakpoint/grid audit
  only, not checked against that specific screenshot or any rendered
  page). None of typecheck/lint/test/build can catch a genuine visual
  regression in either of these. **This is now the single most important
  thing to get for this project, three sessions running** — `776dd63`'s
  real rendered QA remains the only one of the last three visual
  sessions actually seen. If Claude-in-Chrome or equivalent becomes
  available, check, in order: (1) the Dashboard stat-card grid and
  Topbar at 320/375/768px — the operator's specific complaint — (2) the
  rest of `1f9ffdc`'s changes (dialog/form grids, CommandPalette,
  WorkflowRuns resume rows), (3) `8cae377`'s glass-alpha legibility, (4)
  `776dd63`'s original claims (no longer confirmable as a standing
  capability — see below).
  **Status changed from the prior four sessions**: HEAD `776dd63`
  reports the first-ever real rendered visual QA (headless Chromium in a
  scratch environment) and used it to find and fix the actual
  invisible-background root cause — a genuine break from the pattern
  below of reasoning about visual results from code alone. However, this
  session found no repository-committed record of how that browser
  tooling was set up (no Playwright/Puppeteer in `frontend/package.json`,
  no script), so it appears to have been ephemeral to that one sandbox
  and is **not confirmed available again** — treat "get real interactive
  browser verification" as still the top priority, either via
  Claude-in-Chrome or by re-establishing whatever headless setup
  `776dd63` used (and committing it this time, e.g. as a `package.json`
  devDependency + documented script, so it survives to the next
  session).
  - Everything below predates `776dd63` and describes work that, per the
    above, has now had a first real look — but the specific claims below
    (exact opacity/positioning tuning) were made before that fix and
    should be treated as superseded by `776dd63`'s own re-tuning, not as
    still-open questions on the pre-`776dd63` code.
  - The glass/motion design-system pass (glass legibility/contrast,
    ambient-background parallax feel, scroll-reveal timing, backdrop-blur
    performance on Safari): still only reasoned about from code prior to
    `776dd63`; `776dd63`'s own visual QA covered gradient visibility,
    glass-vs-background contrast, and the account popover/heartbeat, but
    not scroll-reveal timing or Safari blur performance specifically.
  - The original `AccountPopover` positioning bug (`right-0` near the
    toolbar's left edge) was superseded by `776dd63`'s portal rewrite,
    which `776dd63` reports as visually confirmed open/on-screen at
    desktop/iPad-portrait/mobile.
  - The `HeartbeatLine` SMIL/multi-cycle rendering and the cream/bronze/
    navy gradient's real visual balance were both re-tuned and visually
    confirmed per `776dd63`'s commit message (see DONE above) — no longer
    an open "reasoned but unseen" item for those two specifically, though
    still worth a second look once standing browser tooling exists.
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
| OpenAI | Alternate LLM provider identity check | `OPENAI_API_KEY` | Optional | **NOT set** (confirmed live: catalog reports `needs_setup`) | `POST /api/v1/integrations/openai/test` returns `503` naming `OPENAI_API_KEY` | Set the var, then "Test connection" → expect `connected: true` (a real `GET /v1/models` call) |
| Anthropic | Alternate LLM provider identity check | `ANTHROPIC_API_KEY` | Optional | **NOT set** (confirmed live) | Same 503 pattern as above | Same as above, naming `ANTHROPIC_API_KEY` |
| Cloudflare | Verify an API token (DNS/Pages actions not yet wired to execute()) | `CLOUDFLARE_API_TOKEN` | Optional | **NOT set** (confirmed live) | Same 503 pattern | Set the var, Test connection calls Cloudflare's own `/user/tokens/verify` endpoint |
| Render | Verify an API key (deploy/service actions not yet wired to execute()) | `RENDER_API_KEY` | Optional | **NOT set** (confirmed live) | Same 503 pattern | Set the var, Test connection calls `GET /v1/owners` |
| GitHub OAuth | Connect a GitHub account (identity check only; issues/PRs not yet wired) | `GITHUB_OAUTH_CLIENT_ID`, `GITHUB_OAUTH_CLIENT_SECRET` | Optional | **NOT set** (confirmed live: catalog reports `needs_setup`) | `GET /api/v1/integrations/oauth/github/authorize` returns `503` naming the missing var(s) | Register an OAuth app on GitHub with callback URL `https://api.thynact.com/api/v1/integrations/oauth/github/callback`, set both vars, then click "Authorize" on the Integrations page and confirm the catalog flips to `connected: true` |
| OAuth redirect base | Where GitHub's (and future OAuth providers') callback points | `AGENT_OS_OAUTH_REDIRECT_BASE_URL` | Optional (defaults to `https://api.thynact.com`, already correct for production) | Uses the default | n/a | Only needs overriding for a non-default backend domain (e.g. local dev) |
| Frontend redirect base | Where the OAuth callback redirects the browser back to after connecting/failing | `AGENT_OS_FRONTEND_URL` | Optional (defaults to `https://app.thynact.com`, already correct for production) | Uses the default | n/a | Only needs overriding for a non-default frontend domain |

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

## AUTH / CORS BOUNDARY — VERIFIED LIVE (partially re-confirmed this session)

- No API key on a protected route → `401 {"detail":"Unauthorized"}` (not
  `503`, confirming the key **is** configured server-side) — re-confirmed
  this session against `GET /api/v1/tools`. Note: the connector catalog
  (`GET /api/v1/integrations`) is the one deliberate exception — see
  PRODUCTION STATUS above.
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
| Dashboard | DONE (this session: hero paragraph removed, 4 metric cards now equal height — see DONE above, visually confirmed) | Metrics, recent audit, quick actions, session activity — all backed by real queries; borderless ambient hero replaces the old bordered brand card, "Dashboard / Live status..." heading removed |
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
| Integrations | DONE (this session) | Flagship Integration Hub UX (search/filters/Currently integrated/Popular/All, neutral setup states, MCP + OAuth + API-key + webhook types unified). 8 connectors READY_FOR_AUTH with real test/verify adapters: n8n, Gemini, PostgreSQL, Redis, OpenAI, Anthropic, Cloudflare, Render. GitHub has a full OAuth2 authorize/callback/disconnect flow (READY_FOR_AUTH, reference implementation for the remaining 11 OAuth catalog-only entries). Every other catalog entry (Slack, Notion, Gmail, GitLab, Jira, HubSpot, Salesforce, Zapier, Make, Discord, Teams, Vercel, Linear, Supabase, Dropbox, OneDrive, Stripe, Google Calendar/Drive) is CATALOG_ONLY, honestly reported as such |
| Audit | DONE, motion pass DONE | Tool events, status, timestamps, table + timeline views (this session). No correlation ID on audit events yet — see NEEDS CREDENTIALS/DATABASE_URL, this requires a migration |
| Health | DONE | Live `/health` + `/ready` + persistence/LLM service map (this session) |
| Settings | DONE (this session: About/brand section added) | API base URL + key (sessionStorage only), theme, About |
| Persistence | PARTIAL — production is memory-only | Code supports Postgres/Redis backends (`app/persistence/`, `app/queue/redis_queue.py`) but production has none configured (see NEEDS CREDENTIALS) |
| Responsive UI | Dashboard + mobile sidebar drawer VERIFIED at 320/360/390/430/640/768/1024px, both themes, HEAD `aad329e` (real rendering + programmatic overflow check, not just code review) | Codebase has solid responsive primitives (`overflow-x-hidden`, `min-w-0`, mobile sidebar drawer, responsive grids). Verified this session: no horizontal overflow at any of the 7 breakpoints, Dashboard cards 1-up below 640px / 2-up 640-1023px / 4-up 1024px+, mobile drawer opens and is fully legible. NOT yet re-verified this way: every other page (Tasks/Workflows/Memory/etc. were audited at the source level in a prior session, and Tools/Settings were spot-checked at desktop width only this session — not at all 7 breakpoints), iPad/tablet-specific AmbientBackground blur cost, AccountPopover touch sizing |
