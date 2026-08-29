# START HERE — THYNACT Project Brain

**Product name:** THYNACT
**Exact brand line:** "Built to Think. Powered to Act."

Never rename, abbreviate, or misspell the product name (do not use "Agent OS",
"PHYRACT", or any other variant in user-facing copy). "Agent OS" is the
original internal/codename still visible in a few non-user-facing places
(Python package name, some dev tooling, git history) — it is being replaced
by THYNACT wherever it is user-visible, not erased from history.

## What this is

THYNACT is a production-grade autonomous agent orchestration platform:
task intake, three-role orchestration (researcher/builder/reviewer),
autonomous multi-specialist runs, a tool registry with approval gates,
semantic + lexical memory, a visual workflow builder/engine, a runtime
layer (retries/circuit breaker/rate limiting), and an external integration
adapter layer (currently n8n).

## Canonical project knowledge — how these 4 files work together

This `PROJECT_BRAIN/` directory is the **only** canonical, persistent
knowledge base for this project across coding sessions. Do not create
additional project-state docs (no `PROGRESS.md`, `NOTES.md`, etc.) —
extend these four instead:

- **00_START_HERE.md** (this file) — architecture, identity, conventions.
  Changes rarely.
- **02_CURRENT_STATE.md** — what is verified DONE / PARTIAL / BLOCKED right
  now. Update after every meaningful session.
- **07_DEFERRED_GOALS.md** — genuinely future/optional work, not current
  blockers. Update when scope is deliberately pushed out.
- **10_NEXT_STEPS.md** — the prioritized execution plan for the next
  session. Update at the end of every session so the next agent can start
  cold.

A new agent picking up this project should read these four files, in this
order, before touching code.

## High-level architecture

```
app.thynact.com  (Cloudflare Pages)  ──HTTPS/JSON──▶  api.thynact.com  (FastAPI on Render, fronted by Cloudflare)
      │                                                        │
      │ X-API-Key, X-Correlation-ID headers                    ├── in-memory or Postgres-backed stores
      │ API key entered by operator, kept in sessionStorage     │   (tasks, workflows, runtime, tools, approvals,
      │ only (never bundled/compiled into the JS build)         │   audit, memory)
      ▼                                                        ├── optional Redis-backed job queue
  React 18 + Vite + TS + Tailwind v4                            ├── LLM provider: mock | gemini
  Framer Motion (page/motion), @xyflow/react (workflow canvas)  └── n8n integration adapter (webhook-based)
  TanStack Query for all server state
```

One Cloudflare Pages Function exists at `functions/api/v1/orchestrate.js` —
a server-side proxy that injects a server-held `AGENT_OS_API_KEY` Cloudflare
secret so orchestration can be triggered without ever putting that key in
browser-delivered JS. It is currently the only endpoint proxied this way;
every other call goes directly from the SPA to `api.thynact.com` using
whichever API key the operator has entered in Settings (stored in
`sessionStorage`, cleared when the tab closes).

## Repository layout

```
app/                    FastAPI backend (Python 3.12)
  api/                  Routers: router.py (tasks), orchestration.py, phase5.py..phase10.py
                         (phase5=autonomous, phase6=tools/approvals/audit, phase7=memory,
                          phase8=workflows, phase9=integrations, phase10=runtime)
  core/                 config.py (Settings/env vars), auth.py (X-API-Key check),
                         correlation.py, readiness.py, orchestrator.py, lifecycle.py
  integrations/         IntegrationAdapter base + factory + n8n.py + status_store.py
  llm/                  mock.py, gemini.py, factory.py
  memory/, workflows/, runtime/, tools/, queue/, persistence/, services/, models/
  main.py               FastAPI app, CORS, exception handlers, /health, /ready, SPA fallback

frontend/               React SPA (Vite, TypeScript, Tailwind v4, pnpm)
  src/pages/            One file per screen (Dashboard, Tasks, Orchestrate, Autonomous,
                         Agents, Workflows, WorkflowRuns, Approvals, Memory, Runtime,
                         Tools, Integrations, Audit, SystemHealth, Settings)
  src/components/layout/  AppShell, Sidebar, Topbar, HealthIndicator, CommandPalette
  src/components/ui/    Design-system primitives (Card, Badge, StatusBadge, BrandMark, ...)
  src/components/workflows/  StepNode, StepEditorDialog (React Flow canvas pieces)
  src/lib/api/          client.ts (fetch wrapper, X-API-Key/X-Correlation-ID), config.ts
                         (sessionStorage-backed API base URL/key), queries.ts (TanStack Query hooks)
  src/index.css         Design tokens (@theme), color tokens, animation keyframes,
                         global prefers-reduced-motion override

functions/api/v1/orchestrate.js   Cloudflare Pages Function (server-side API-key proxy)
tests/                  Backend pytest suite (pytest, one file per phase/subsystem)
migrations/             SQL migrations for the Postgres-backed stores
infra/                  Docker Compose for local n8n and platform services
scripts/                Dev/ops scripts
PROJECT_BRAIN/          This canonical knowledge base
```

## Deployment architecture (verified)

- **Frontend**: Cloudflare Pages, auto-deploys from `origin/main`. Build
  uses **pnpm** (not npm — npm ci previously had a bug on this project) and
  Node is pinned via `frontend/.node-version` = `20.19.5`. No `wrangler.toml`
  in-repo; Pages project config (build command, Node version, env) lives in
  the Cloudflare dashboard.
- **Backend**: FastAPI on **Render**, fronted by Cloudflare for the
  `api.thynact.com` domain (confirmed via `rndr-id`/`x-render-origin-server:
  uvicorn` response headers behind `server: cloudflare`). Auto-deploys from
  `origin/main` — verified in this session: a push to `main` was live and
  serving the new code within roughly 1–2 minutes. No `render.yaml` in-repo;
  Render service config lives in the Render dashboard. A root `Dockerfile`
  exists (`python:3.12-slim`, installs `app/` via `pyproject.toml`, runs
  `uvicorn app.main:app`) — unconfirmed whether Render actually builds from
  this Dockerfile or uses a native Python buildpack; mark this UNVERIFIED
  until checked against the Render dashboard.
- Do **not** attempt to run FastAPI inside Cloudflare Pages — Pages is
  static hosting + edge Functions only.

## Coding & deployment safety conventions (from CLAUDE.md, still binding)

- GitHub is the source of truth; treat any local/Replit environment as
  disposable.
- Never put `AGENT_OS_API_KEY`, `GEMINI_API_KEY`, or any other secret in
  frontend code, the compiled JS bundle, or committed files.
- Prefer small, reversible commits; run tests/checks before every commit;
  push to `origin/main` only once verified.
- Never fake a successful external connection/integration — report
  "not configured" and name the missing environment variable instead.
- Never print, log, or commit secret values — variable **names** only.
