# NEXT STEPS — prioritized execution plan

Read root `CLAUDE.md` first (permanent rules), then `00_START_HERE.md` and
`02_CURRENT_STATE.md`. Run `bash scripts/project_doctor.sh` before planning —
it answers most environment questions in seconds.

Rewritten 2026-08-31 after the first real PostgreSQL/pgvector/Redis validation
and the first portable browser QA. Several long-standing blockers are now
CLOSED; do not re-litigate them.

## CLOSED — do not redo these

- ~~Browser tooling / visual QA~~ — `pnpm screenshot` is portable now (no
  Replit variable), fails on horizontal overflow, and can seed an operator
  session to render authenticated pages. Chromium resolves automatically.
- ~~"Glass-alpha legibility never rendered"~~ — rendered in light and dark;
  legible. ~~"Mobile responsive fix never seen"~~ — confirmed correct at 390px.
- ~~"Migrations never run against a real Postgres"~~ — all 5 applied to real
  PG16 + pgvector 0.6.0, idempotency confirmed, HNSW index verified.
- ~~"Postgres/Redis code paths never exercised for real"~~ — `/ready` returned
  real `database: ok` / `queue: ok`; task persistence, pgvector-scored memory
  search and orchestration all ran through the durable path.
- ~~Environment rediscovery each session~~ — `scripts/bootstrap_claude_cloud.sh`
  + `scripts/project_doctor.sh`.

## Manual actions only the operator can take

Everything else below can be done by an agent. Ranked — ask for **one** at a
time, highest first.

1. **Buy/choose the permanent THYNACT domain** (nine-point plan item 1). This is
   the top blocker: it gates stable production/staging URLs, permanent OAuth
   redirect and webhook callback URLs, and therefore every OAuth connector
   including Google. Until it exists, mark OAuth work `STABLE_DOMAIN_REQUIRED`
   and do not repeat the tunnel → callback → restart loop.
2. **Provision production Postgres + Redis** and set `DATABASE_URL` /
   `REDIS_URL` on Render (paid-infrastructure decision — needs explicit
   approval; do not provision without it). The code path is now proven, so this
   is purely a provisioning + env-var step.
3. Provide a scoped `AGENT_OS_API_KEY` value if authenticated live smoke tests
   against `api.thynact.com` are wanted.
4. Optional connector credentials, each unlocking exactly one connector:
   `GEMINI_API_KEY` (+ `AGENT_OS_LLM_PROVIDER=gemini`), `OPENAI_API_KEY`,
   `ANTHROPIC_API_KEY`, `CLOUDFLARE_API_TOKEN`, `RENDER_API_KEY`,
   `N8N_BASE_URL`, `MAKE_WEBHOOK_URL`, and the OAuth pairs for GitHub, GitLab,
   Slack and Notion.

## 0. Deployment state — read before shipping anything

Root `CLAUDE.md` §9 now requires the full implement→test→build→deploy→verify
pipeline on every meaningful change. Current reality, verified 2026-08-31:

- **No staging environment exists.** Cloudflare Pages (frontend) and Render
  (backend) both auto-deploy from `origin/main` only. So the "deploy to
  staging" step has no target today — do not claim it ran. Creating staging is
  nine-point item 2 and is now the blocker for satisfying §9 properly.
- **Pushing/merging to `main` is a production deploy.** Current work sits on
  `claude/thynact-env-audit-fjinfj` and was deliberately **not** merged: no
  production-deploy authorization has been given. Ask before merging.
- This session held no `CLOUDFLARE_API_TOKEN` / `RENDER_API_KEY`, so it could
  not drive or inspect either provider's deploy pipeline directly; production
  verification is limited to public `curl` of `/health`, `/ready` and the
  served asset hash.
- Post-deploy migration runs are manual (`scripts/migrate.py`) — see §9.

## 1. Production persistence — READY, blocked only on provisioning
The exact sequence is now proven locally, in this order:
1. Set `DATABASE_URL` (and `REDIS_URL`) on Render.
2. `uv run python scripts/migrate.py` **once, by hand** — nothing runs it
   automatically. Requires pgvector on the managed instance: confirm the
   provider offers it (most managed Postgres services do; it is an extension,
   not a fork) **before** choosing the provider.
3. Flip `AGENT_OS_{MEMORY,TASK,WORKFLOW,WORKFLOW_DEFINITION,RUNTIME,TOOL}_BACKEND`
   to `postgres` and `AGENT_OS_QUEUE_BACKEND=redis`.
4. Redeploy, then expect `/ready` → real `database`/`queue` checks and
   `/health` `backends` showing postgres/redis instead of memory.
Until then every task/workflow/approval/audit record is lost on each restart.

## 2. Highest-value agent work available with no credentials
In rough priority order:
- ~~Finish the visual sweep~~ **DONE** — all 15 routes rendered at 1440 and
  390 against a live backend; two real Workflows-canvas defects found and
  fixed. Remaining visual work is narrower: 768px/tablet, light theme on more
  than the two pages checked, and real touch/drag behaviour on the React Flow
  canvas (which still cannot be assessed from screenshots alone).
- **Postgres-backed correctness under real data.** The suite covers the
  postgres paths with fakes; now that a real database is one script away, add
  targeted tests that run against it for the trickiest queries (memory hybrid
  ranking, workflow run resume, approval single-use semantics).
- ~~Audit correlation-ID quick-copy~~ **DONE** (migration 006, verified
  against real PostgreSQL). Natural follow-on: thread the same correlation id
  through workflow runs and runtime executions, whose types already declare a
  `correlation_id` field, so one id traces a whole multi-step run.
- **Observability foundations** (nine-point item 8) — structured request logs
  with correlation id, timing, tenant placeholder; no secrets in logs.
- Bespoke UI follow-ups in `07_DEFERRED_GOALS.md` — optional visual depth only,
  never allowed to block correctness work.

## 3. Standing verification commands
- Backend: `uv run pytest tests/ -q` (230 passing as of 2026-08-31).
- Frontend from `frontend/`: `pnpm typecheck && pnpm lint && pnpm test &&
  pnpm build` (48 passing, 2 pre-existing lint warnings).
- Production: `curl https://api.thynact.com/health` and `/ready`; compare the
  served frontend asset hash against a fresh local `pnpm build`.

## 4. Final docs update — recurring
End every session by updating `02_CURRENT_STATE.md` with what is newly verified
and rewriting this file's priorities. Commit `PROJECT_BRAIN/` separately from
functional changes. Update root `CLAUDE.md` only when a **permanent rule**
changes, never for state.

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
