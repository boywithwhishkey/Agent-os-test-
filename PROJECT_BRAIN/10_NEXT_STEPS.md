# NEXT STEPS — prioritized execution plan

Read `00_START_HERE.md` and `02_CURRENT_STATE.md` first. This is the
concrete plan for the next work session, in priority order. Update this
file at the end of every session so the next agent can start cold.

## Manual actions only the operator can take

Nothing else in this file requires the operator directly — everything
below this point can be done by an agent. These specifically cannot:

1. **Provide a production API key value** to a session, so it can run
   authenticated live smoke tests against `api.thynact.com` (or run the
   flows manually and report back what happened).
2. **Provide `DATABASE_URL`** (a Postgres connection string) if durable
   persistence is wanted — this may mean provisioning a Postgres instance,
   which is a paid-infrastructure decision requiring explicit approval.
3. **Provide `REDIS_URL`** if a durable job queue is wanted — same
   paid-infrastructure caveat.
4. **Provide `N8N_BASE_URL`** (+ optional auth vars) if the n8n connector
   should go live — the code is ready, it just has nothing to point at.
5. **Provide `GEMINI_API_KEY`** (and set `AGENT_OS_LLM_PROVIDER=gemini`)
   if real LLM reasoning is wanted instead of the deterministic mock.
6. **Provide `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`** if verifying those
   as alternate LLM providers is wanted (adapters are READY_FOR_AUTH).
7. **Provide `CLOUDFLARE_API_TOKEN` / `RENDER_API_KEY`** if verifying
   those platform accounts is wanted (adapters are READY_FOR_AUTH).
8. **Register a GitHub OAuth app** (callback URL
   `https://api.thynact.com/api/v1/integrations/oauth/github/callback`)
   and provide `GITHUB_OAUTH_CLIENT_ID`/`GITHUB_OAUTH_CLIENT_SECRET` if
   connecting a GitHub account is wanted — this is the only OAuth
   connector implemented so far (READY_FOR_AUTH).
9. ~~Connect browser automation tooling~~ **RESOLVED, HEAD `aad329e`** —
   no longer needs the operator. `frontend/scripts/screenshot.mjs`
   (`pnpm screenshot <url> <outPath> [theme] [width] [height]`) gives any
   future session real rendered screenshots via Playwright pointed at the
   Replit-provided `$REPLIT_PLAYWRIGHT_CHROMIUM_EXECUTABLE` binary — see
   `02_CURRENT_STATE.md`'s "BLOCKED (historical — RESOLVED...)" section
   for why a plain `chromium.launch()` doesn't work in this container.
   `playwright` is now a committed `devDependency`, so this survives to
   the next session unlike `776dd63`'s one-off setup. Item 3 below is no
   longer blocked — use this tool for it.

## 1. Production backend/API — STATUS: VERIFIED, monitor only
- `/health` and `/ready` are live and correct. CORS preflight for
  `X-API-Key`/`X-Correlation-ID` from `app.thynact.com` is fixed and
  verified live. Nothing to do here unless a regression is found.

## 2. Auth/CORS/connectivity verification — STATUS: VERIFIED, one gap remains
- TODO / VERIFY: confirm whether Render's `environment` should be set to
  `production` (currently reports `development` in `/health`) — cosmetic,
  low priority, but worth a deliberate decision rather than leaving it
  unset by accident.
- TODO / NEEDS CREDENTIAL: this session had no production API key, so
  authenticated endpoints were verified via the local test suite only, not
  against the live API directly. Next session: either get a scoped
  read-only test key to run a handful of live smoke calls, or have the
  operator run through the flows manually in production and report back.

## 3. Real feature E2E verification — STATUS: TODO, no longer blocked
- **No longer needs the operator or Claude-in-Chrome** — use
  `pnpm screenshot <url> <outPath> [theme] [width] [height]`
  (`frontend/scripts/screenshot.mjs`, added HEAD `aad329e`) with the dev
  server running (`pnpm dev`, port 3000). This session used it for
  Dashboard + the mobile sidebar drawer + a spot-check of Tools/Settings
  only (see `02_CURRENT_STATE.md`'s DONE entry for HEAD `aad329e`) — the
  full sweep below is still outstanding.
- For each of Dashboard, Tasks, Orchestrate, Autonomous, Agents,
  Workflows, Workflow Runs, Approvals, Memory, Runtime, Tools,
  Integrations, Audit, Health, Settings — verify navigation, forms,
  dialogs, loading/empty/success/error states, real API traffic, and a
  clean browser console (no errors from our own code — the script writes
  `<outPath>.errors.txt` automatically when there are any; note that
  `net::ERR_CONNECTION_REFUSED` to `localhost:8000` is expected with no
  local backend running, not a real error).
- Do not mark any page "browser-verified" without this step actually
  happening.
- **Highest-priority single check now (HEAD `8cae377`)**: the glass-alpha
  retune that cut `.glass-panel` to ~0.15/0.16 alpha and `.glass-focus`
  (dialogs/drawers/popovers/dropdowns) to ~0.4/0.55 — chosen entirely by
  reasoning about contrast, never rendered. Specifically check: text
  legibility on `Card`/`MetricCard` at the new low alpha over the busiest
  parts of `AmbientBackground` (where the bronze/navy glow blobs
  overlap), whether `.glass-focus` modals/drawers are still comfortably
  readable over real page content at the new lower opacity (this is the
  main legibility risk — it dropped the most, dark 0.88->0.4), and the
  new `.glass-field` `Input`/`Textarea`/`Select` tier reading as a
  distinct clickable target nested inside an already-translucent `Card`.
  Also confirm the light-mode gradient (new this session, reusing the
  cream/bronze/navy tokens at 7-55% color-mix vs dark's 16-48%) actually
  looks like a deliberate soft wash and not a washed-out accident.
- **Still true, one layer down**: `776dd63`'s invisible-background
  root-cause fix (removing `bg-surface-canvas` from `AppShell`'s root),
  portal `AccountPopover`, and multi-cycle `HeartbeatLine` were reported
  as actually rendered and visually confirmed in that session's own
  headless-Chromium sandbox — but this session found no repo-committed
  record of how that tooling was set up, so treat it as re-confirmed only
  once real browser tooling is connected again in a persistent way (see
  manual-action item 9 above), not as a standing capability.
  **If browser tooling becomes available, spend it here first** — every
  session since HEAD `70cf378` has added more code-reasoned-but-unseen
  visual changes on top of the last, and this session added the biggest
  opacity change yet.

## 4. Connectors/integrations — STATUS: code-complete, NEEDS CREDENTIALS to go live
- DONE (this session): Integration Hub UX overhaul (neutral setup states,
  unified catalog+MCP gallery, search/filters); real adapters for Gemini,
  PostgreSQL, Redis, OpenAI, Anthropic, Cloudflare, Render (all
  READY_FOR_AUTH); a full OAuth2 authorize/callback/disconnect flow, with
  GitHub as the reference implementation (READY_FOR_AUTH). Fixed a real
  404 bug where Gemini/PostgreSQL/Redis's "Test connection" button did
  nothing but fail. See 02_CURRENT_STATE.md DONE section for the full
  list.
- DONE (prior session): n8n completeness audit — registration, config
  validation, test-connection endpoint, auth header handling, timeout,
  correlation-ID passthrough, network-failure handling, non-2xx handling,
  and non-JSON response handling are all implemented and tested. n8n is
  genuinely production-ready code-wise.
- NEEDS CREDENTIALS (all optional, none blocking): `N8N_BASE_URL`,
  `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`,
  `CLOUDFLARE_API_TOKEN`, `RENDER_API_KEY`, and
  `GITHUB_OAUTH_CLIENT_ID`/`_SECRET` — see 02_CURRENT_STATE.md's
  "PRODUCTION DEPENDENCY / CREDENTIAL AUDIT" table for exactly what each
  does and how to verify it once set. Once any is set, use "Test
  connection" (or "Authorize" for GitHub) on the Integrations page and
  confirm the catalog entry flips to `connected: true`.
- NEXT (only when there's concrete product need, not speculatively): the
  next OAuth provider following GitHub's pattern (see
  07_DEFERRED_GOALS.md for exactly which file/fields to touch) — Slack or
  Notion are the most likely candidates given they're both `popular:
  true` in the catalog. Do not add another connector adapter or OAuth
  provider without a real reason.

## 5. Persistence/runtime — STATUS: NEEDS CREDENTIALS
- NEEDS CREDENTIAL: `DATABASE_URL` (Postgres) to move
  `AGENT_OS_MEMORY_BACKEND` / `AGENT_OS_TASK_BACKEND` /
  `AGENT_OS_WORKFLOW_BACKEND` / `AGENT_OS_RUNTIME_BACKEND` /
  `AGENT_OS_TOOL_BACKEND` / `AGENT_OS_WORKFLOW_DEFINITION_BACKEND` off
  `memory` and onto durable storage in production. Until this is set,
  every task/workflow/approval/audit record is lost on every Render
  restart or redeploy.
- NEEDS CREDENTIAL: `REDIS_URL` to move `AGENT_OS_QUEUE_BACKEND` off
  `memory` onto a real job queue.
- Exact sequence once `DATABASE_URL` exists (do not skip the manual
  migration step — nothing runs it automatically, see 00_START_HERE.md):
  1. `python scripts/migrate.py` (applies `migrations/*.sql`, idempotent).
  2. Flip the relevant `AGENT_OS_*_BACKEND` env vars to `postgres` (and
     `AGENT_OS_QUEUE_BACKEND=redis` once `REDIS_URL` exists too) on Render.
  3. Redeploy, then `curl https://api.thynact.com/ready` → expect real
     `database`/`queue` checks (not an empty `checks: {}`), and `/health`
     → `backends` map should show `postgres`/`redis` instead of `memory`.
- Do not provision Postgres/Redis infrastructure without the user's
  explicit approval — this is a paid-infrastructure decision.

## 6. Premium UI completion — STATUS: foundation DONE + retuned twice since, bespoke follow-ups remain
Built originally at HEAD `70cf378` (`GlassSurface`, `AmbientBackground`,
`lib/motion.ts`, `ScrollReveal`/`StaggerGroup`, `AccountPopover`,
`Card`/`MetricCard` cascading to 14+ pages, app shell). Fixed at HEAD
`776dd63` (the gradient was rendering behind a hidden opaque layer the
whole time). Retuned at HEAD `8cae377` (this session): alpha cut further
toward ~0.04-0.16 for cards/sections per an updated brief, new
`.glass-field` tier for forms/inputs, light-mode gradient added. See
00_START_HERE.md's "Frontend design system" section and
02_CURRENT_STATE.md's DONE entries for detail on each.
- **Highest priority next**: actual interactive/visual QA — see item 3
  above. Nothing since `70cf378` has been seen rendered in a real browser
  except `776dd63`'s one-time headless-Chromium sandbox session (not
  reproducibly available). Everything else, including this session's
  biggest-yet opacity change, has only been verified via
  typecheck/lint/test/build.
- Remaining bespoke follow-ups (see 07_DEFERRED_GOALS.md's new "glass/
  motion design-system — bespoke follow-ups" section for the full,
  prioritized list): Orchestration data-flow particles, Autonomous
  computation-graph layout, Memory spatial graph movement, Workflows edge/
  minimap polish + the still-deferred context side panel, Runtime's
  circuit-breaker diagram, Audit's correlation-ID quick-copy (needs a
  `DATABASE_URL`-backed migration).
- Keep using the existing design system (`frontend/src/components/ui/*`,
  the `@theme` tokens/keyframes + glass utilities in `index.css`,
  `lib/motion.ts`, Framer Motion, React Flow) — do not introduce new UI
  libraries, and do not re-introduce opaque bordered cards where a
  `Card`/`GlassSurface` already exists.

## 7. Responsive/browser QA — STATUS: TODO (needs browser tooling) — TOP PRIORITY
- BLOCKED on the same browser tooling as step 3. Once available, check
  320 / 360 / 375 / 390 / 414 / 430 / 768 / 1024px, with particular
  attention to iPad portrait/landscape and the Workflows canvas (React
  Flow touch behavior, Controls/MiniMap sizing on small screens). Check
  `document.documentElement.scrollWidth` vs `clientWidth` at each width —
  must be equal (no page-level horizontal scrollbar).
- Requirements to verify: no horizontal overflow, no clipped modals/
  drawers, touch-friendly tap targets, mobile nav works, tables/cards
  degrade sensibly, charts resize, command palette usable on mobile.
- **HEAD `1f9ffdc` (this session) — first thing to check, operator-
  reported issue**: the operator checked the live site on an actual
  phone and reported the Dashboard stat-card grid squeezed into 2 narrow
  columns, a cramped Topbar, and poor text wrapping. Fixed via a
  source-level audit only (grid-cols-1 base classes, Topbar icon-only
  search + compact `HealthIndicator` below `sm`, several other
  `grid-cols-2`→responsive fixes — full list in 02_CURRENT_STATE.md's
  DONE entry for this HEAD) — **none of it has been seen rendered**.
  Specifically verify: Dashboard at 320-375px (1 stat-card column, hint
  text not wrapping awkwardly), Topbar at the same widths (hamburger +
  account + search icon + health pill + theme + settings all fit on one
  row without collision), and that nothing regressed at 1024px+ desktop
  (all the fixes were additive `sm:`/base changes, not `lg:`+ changes,
  so desktop classes are believed unchanged — believed, not seen).
- Also still open from prior sessions: the `AccountPopover` sheet/
  popover on narrow viewports, and whether stacking multiple
  `backdrop-filter: blur()` glass layers causes any visible jank while
  scrolling on real iPad hardware (code-level review can't assess GPU
  compositing cost) — and now also the `8cae377` glass-alpha legibility
  question (see item 3/6 above).

## 8. Regression tests — STATUS: DONE as of this session, re-run before next push
- Before the next commit, re-run: `python -m pytest tests/ -q` (backend,
  208 tests — not re-run this session since no backend code changed,
  same as last session), `pnpm typecheck && pnpm lint && pnpm test &&
  pnpm build` (frontend, 48 tests, run from `frontend/`). All were green
  as of commit `1f9ffdc`.

## 9. Production verification — STATUS: VERIFIED (deploy only, not visual) as of this session
- Re-verify after any new push: `curl https://api.thynact.com/health`,
  `curl https://api.thynact.com/ready`, and compare the frontend's served
  asset hash against a fresh local `pnpm build` to confirm Cloudflare
  actually deployed the latest commit (see 02_CURRENT_STATE.md
  "PRODUCTION STATUS" for the exact method used this session). Reconfirmed
  this session (HEAD `1f9ffdc`): Cloudflare deployed correctly
  (`index-CwgnVrCF.js` matched a fresh local build byte-for-byte);
  `/health` unaffected since no backend code changed this session. This
  confirms the code shipped, not that it renders correctly — see item 7.
- **Environment note reconfirmed this session**: `git push origin main`
  failed once at the very start with the same "Invalid username or
  token" error documented below — `gh auth setup-git` fixed it
  immediately, and the fix held for a second push later in the same
  session without needing to be repeated. Still expect to need it once
  per fresh session.

## 10. Final docs update — STATUS: recurring
- At the end of every session: update `02_CURRENT_STATE.md` with what's
  newly verified DONE/PARTIAL/BLOCKED, move anything newly completed out
  of this file and out of `07_DEFERRED_GOALS.md`, and rewrite this file's
  priorities for the next session. Commit `PROJECT_BRAIN/` on its own
  (don't mix it into a functional-change commit).

## Requirements to keep enforcing on every future UI change

- Brand: **THYNACT** / "Built to Think. Powered to Act." — exact spelling,
  used sparingly (one brand moment per major surface, not repeated
  everywhere).
- API status indicator (top-right): online = green double-beat heartbeat +
  expanding ring (~1.8s), connecting = amber breathing (~2.2s), offline =
  red slow static-friendly pulse (~2.4s) — all must degrade to static under
  `prefers-reduced-motion`.
- Overall frontend direction: premium, futuristic AI operating system feel;
  rich but performant (`transform`/`opacity` only) animation; strong
  responsiveness across desktop, tablet/iPad, and mobile.
- Design system (this session on): no new opaque bordered cards — use
  `Card`/`GlassSurface` (glass-panel/soft/ambient/focus) and
  `border-hairline`, not `bg-surface-raised` + `border-surface`, for
  page-level content surfaces. New section entrances use
  `ScrollReveal`/`StaggerGroup` from `components/ui/ScrollReveal.tsx`, new
  drawers/dialogs use `drawerMotion`/`modalMotion` from `lib/motion.ts` —
  don't hand-roll new ad hoc Framer Motion variants for these. The
  `AccountPopover` only surfaces real operator-session state; never add a
  field there that isn't backed by an actual backend/local concept.
