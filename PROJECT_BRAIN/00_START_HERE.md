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
adapter layer supporting webhook (n8n), API-key (Gemini, OpenAI,
Anthropic, Cloudflare, Render, PostgreSQL, Redis), OAuth2 (GitHub, with
the same pattern ready for more), and generic remote MCP server
connectors — see 02_CURRENT_STATE.md's Integrations row for exactly which
of these are READY_FOR_AUTH vs. still catalog-only.

## Durable rules live in root `CLAUDE.md`

Root `CLAUDE.md` is the permanent operating contract (priorities, security
invariants, connector/validation rules, environment facts, autonomy rules). It
is loaded automatically every session — read it, and keep it free of changing
state. Two helpers back it up:

- `bash scripts/bootstrap_claude_cloud.sh` — idempotent environment setup
  (uv sync, pnpm install, native Postgres + pgvector, Redis, migrations,
  browser check). Safe to re-run; never destructive.
- `bash scripts/project_doctor.sh` — report-only diagnostics. Prints credential
  **names** and whether they are set, never values.

Facts that change (what is DONE/BLOCKED, connector status, test counts) belong
in this directory, not in `CLAUDE.md`.

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
  integrations/         IntegrationAdapter base + factory + status_store.py;
                         n8n.py, gemini.py, postgresql.py, redis.py, openai.py,
                         anthropic.py, cloudflare.py, render.py, github.py adapters;
                         mcp/ (remote MCP client+store); oauth/ (generic OAuth2
                         authorize/callback/state/connection-store framework)
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
- **Database migrations are manual, not automatic.** `app/persistence/
  migrations.py` (`run_migrations`) applies pending `.sql` files from
  `migrations/` under a Postgres advisory lock, tracked in a
  `schema_migrations` table — it's idempotent and safe to re-run, but
  nothing in `app/main.py`'s startup path calls it. It only runs via
  `python scripts/migrate.py` (reads `DATABASE_URL` from settings) —
  run this by hand after `DATABASE_URL` is set and before switching any
  `AGENT_OS_*_BACKEND` env var to `postgres`. The runner's idempotency
  logic has a unit test (`tests/test_group2c_reliability.py`, using a
  fake DB) but the actual `.sql` files have not been executed against a
  real Postgres instance in any session with access to this repo.

## Frontend design system — "infinite canvas" glass/motion upgrade

THYNACT's frontend runs on a shared glass-material + motion system, not
page-by-page bespoke styling. A new agent touching UI should build on these
primitives rather than reinventing bordered cards:

- **Load-bearing fact (HEAD `776dd63`): `AppShell`'s root element must
  never carry an opaque background class.** From `70cf378` through
  `8a9dd81`, `AppShell`'s root `div` had `bg-surface-canvas` (fully
  opaque) painted directly over `body`, silently hiding the entire
  ambient-gradient system underneath every glass surface — three
  sessions of gradient/glass-alpha retuning happened on a layer nothing
  could see. Fixed by removing it; if the background ever looks flat
  again, check this first before re-tuning gradient math.
- **Glass depth hierarchy** (`frontend/src/index.css` — `.glass-ambient`,
  `.glass-soft`, `.glass-panel`, `.glass-focus`): increasing opacity/blur/
  shadow, used instead of opaque `bg-surface-raised` + bright borders.
  Dark-mode background alpha as of `776dd63` (`.dark .glass-*` rules,
  `index.css` ~L184-232): `.glass-ambient` 0.2, `.glass-soft` 0.34,
  `.glass-panel` 0.5, `.glass-focus` 0.88 (dialogs/drawers, intentionally
  left highest for legibility — untouched by `776dd63`).
  `border-hairline` (very low-opacity tonal edge) replaces `border-surface`
  wherever a surface only needs a whisper of separation rather than a
  visible outline; `border-surface` itself is untouched and still used for
  genuinely interactive chrome (buttons, inputs, tabs) where a visible edge
  is the correct affordance, not "boxiness". As of HEAD `8a9dd81` this
  sweep is complete app-wide: the only remaining `border-surface`/
  `bg-surface-raised` usages are that interactive chrome
  (`Button`/`Input`/`Badge`/`Tabs`/`Toast`) and the React Flow `MiniMap`
  (needs an opaque background to stay legible over the canvas). A future
  "remove hard borders" request should start from that premise — grep for
  `border-surface` first rather than assuming there's more to do.
- **`GlassSurface`** (`components/ui/GlassSurface.tsx`) — the base
  translucent-pane primitive (`level: ambient|soft|panel|focus`).
- **`Card`/`MetricCard`** (`components/ui/Card.tsx`, `MetricCard.tsx`) were
  converted to `glass-panel`/`glass-soft` — since `Card` alone is used
  across 14+ pages, this is the main lever that removed "page → bordered
  card → bordered card" boxiness app-wide without a bespoke pass on every
  page.
- **`AmbientBackground`** (`components/layout/AmbientBackground.tsx`) —
  mounted once in `AppShell`; a fixed, `pointer-events-none` layer behind
  the whole app shell: a faint technical grid + two slow-drifting mesh
  gradient glows + ~10 sparse floating data points, with a scroll-driven
  parallax (background moves slower than foreground) via Framer Motion's
  `useScroll`/`useTransform`/`useSpring`. Respects `useReducedMotion`
  (disables parallax and the floating points, not just CSS animation-
  duration).
- **Motion tokens** (`lib/motion.ts`) — the single reusable motion
  language: `pageEnter`, `sectionReveal`, `staggerContainer`/`staggerItem`,
  `glassAppear`, `drawerMotion`/`sheetMotion`/`modalMotion`, `hoverFloat`,
  `fadeThrough`, `metricReveal`. Springs are tuned high-damping (precise,
  not bouncy) per the brief's "expensive, technical, fluid — not
  cartoonish" direction.
- **`ScrollReveal`/`StaggerGroup`/`StaggerItem`**
  (`components/ui/ScrollReveal.tsx`) — `whileInView`-based section/stagger
  entrances, fire once, no scroll-jacking, native scrolling preserved.
  Requires an `IntersectionObserver` — jsdom has none, so
  `frontend/src/test/setup.ts` installs a no-op mock; a future agent
  hitting `"IntersectionObserver is not defined"` in a frontend test should
  look there first, not assume a real regression.
- **`AccountPopover`** (`components/layout/AccountPopover.tsx`) — the
  circular profile control beside the sidebar hamburger. THYNACT has no
  backend user-account system, only the operator's local API-key session
  (`lib/api/config.ts`, sessionStorage-only) — the popover surfaces exactly
  that (configured/not, base URL, "Clear session") plus links to
  Settings/Integrations. Don't add fields here that don't map to a real
  backend concept.
- Drawers/dialogs/the command palette use `glass-focus` + spring-based
  entrance (`drawerMotion`/`modalMotion`) instead of opaque rectangles +
  linear tweens.
- **API heartbeat line** (`components/ui/HeartbeatLine.tsx`) — replaces a
  blinking dot with an ECG-style trace: online is a seamlessly looping
  waveform via SVG SMIL `<animateTransform>` (not CSS — SMIL translate
  values stay correct in the SVG's own coordinate system regardless of
  how the element is scaled, unlike `transform: translateX()` in px),
  connecting is the same waveform static + breathing opacity, offline is
  a calm straight line with no motion implied. Used in `HealthIndicator`
  (top-right pill) and Dashboard's API status `MetricCard` (via its
  optional `graphic` slot). Checks Framer Motion's `useReducedMotion`
  itself, since SMIL animation isn't touched by the global CSS
  `prefers-reduced-motion` override that neutralizes everything else.
- **Ambient background color direction**: `--color-ambient-cream`
  (`#f5e9dd`), `--color-ambient-bronze` (`#a67c52`), and
  `--color-ambient-navy` (`#122d70`) — a specific reference palette given
  in a later session — drive a faint cream/bronze/deep-navy
  radial-gradient `body` background over a near-black foundation, plus
  `AmbientBackground`'s mesh glows/data points, in dark mode. These
  superseded an earlier `--color-ambient-wine` (deep red) direction from
  the session in between — if you see `ambient-wine` referenced anywhere
  it's stale, the palette is cream/bronze/navy now. All three
  `ambient-*` tokens are deliberately separate from `--color-accent-*`
  (interactive/status tokens, especially `--color-accent-red` which stays
  reserved for real error/offline status) — never repurpose a status
  token for decoration, and never use an `ambient-*` token for status.

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
