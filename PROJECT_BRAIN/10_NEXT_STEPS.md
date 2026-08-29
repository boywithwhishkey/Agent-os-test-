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
6. **Connect browser automation tooling** (e.g. Claude in Chrome) to this
   session if interactive/visual QA is wanted — everything reachable
   without it (tests, typecheck, lint, build, curl-level API checks,
   static responsive review) has already been done.

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

## 3. Real feature E2E verification — STATUS: TODO (needs browser tooling)
- BLOCKED on browser automation: connect Claude-in-Chrome (or equivalent)
  and, for each of Dashboard, Tasks, Orchestrate, Autonomous, Agents,
  Workflows, Workflow Runs, Approvals, Memory, Runtime, Tools,
  Integrations, Audit, Health, Settings — verify navigation, forms,
  dialogs, loading/empty/success/error states, real API traffic, and a
  clean browser console (no errors from our own code).
- Do not mark any page "browser-verified" without this step actually
  happening.

## 4. Connectors/integrations — STATUS: code-complete, NEEDS CREDENTIAL to go live
- DONE: full n8n completeness audit this session — registration, config
  validation, test-connection endpoint, auth header handling, timeout,
  correlation-ID passthrough, network-failure handling, non-2xx handling,
  and non-JSON response handling are all implemented and tested (see
  02_CURRENT_STATE.md "PRODUCTION DEPENDENCY / CREDENTIAL AUDIT" and the
  n8n audit bullet in DONE). n8n is genuinely production-ready code-wise.
- NEEDS CREDENTIAL: `N8N_BASE_URL` (+ optionally
  `N8N_WEBHOOK_AUTH_HEADER`/`N8N_WEBHOOK_AUTH_VALUE`) to move n8n from
  "not configured" to a real, testable connection. Once set, run
  "Test connection" from the Integrations page and confirm `connected:
  true` with a real latency figure.
- Do not add another connector adapter unless there's a concrete product
  need (see 07_DEFERRED_GOALS.md).

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

## 6. Premium UI completion — STATUS: mostly DONE, small remainder
Essentially every page in the product brief now has a dedicated
motion/visualization pass: Dashboard, API heartbeat, Orchestrate,
Autonomous, Memory (score bar + relationship graph), Runtime (breaker
badge + rate gauge), System Health (persistence map), Audit (timeline
view), Workflows (3/4 flagship features). See 02_CURRENT_STATE.md DONE
section for the full list with implementation notes.
- Remaining: Workflows' context side panel (deliberately deferred — see
  07_DEFERRED_GOALS.md), Runtime's circuit-breaker *diagram* (richer than
  the current badge, optional), Audit's correlation-ID quick-copy (needs
  a `DATABASE_URL`-backed migration), Agents/Approvals/Tools haven't had
  a dedicated additional pass (lower priority, already consistent with
  the shared design system).
- Keep using the existing design system (`frontend/src/components/ui/*`,
  the `@theme` tokens/keyframes in `index.css`, Framer Motion, React Flow)
  — do not introduce new UI libraries.

## 7. Responsive/browser QA — STATUS: TODO (needs browser tooling)
- BLOCKED on the same browser tooling as step 3. Once available, check
  375 / 430 / 768 / 820 / 1024 / 1180 / 1440px, with particular attention
  to iPad portrait/landscape and the Workflows canvas (React Flow touch
  behavior, Controls/MiniMap sizing on small screens).
- Requirements to verify: no horizontal overflow, no clipped modals/
  drawers, touch-friendly tap targets, mobile nav works, tables/cards
  degrade sensibly, charts resize, command palette usable on mobile.

## 8. Regression tests — STATUS: DONE as of this session, re-run before next push
- Before the next commit, re-run: `uv run pytest tests/ -q` (backend, 137
  tests), `pnpm typecheck && pnpm lint && pnpm test && pnpm build`
  (frontend, 25 tests, run from `frontend/`). All were green as of commit
  `87d32a1`.

## 9. Production verification — STATUS: VERIFIED as of this session
- Re-verify after any new push: `curl https://api.thynact.com/health`,
  `curl https://api.thynact.com/ready`, and compare the frontend's served
  asset hash against a fresh local `pnpm build` to confirm Cloudflare
  actually deployed the latest commit (see 02_CURRENT_STATE.md
  "PRODUCTION STATUS" for the exact method used this session).

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
