# NEXT STEPS — prioritized execution plan

Read root `CLAUDE.md` first (permanent rules), then `00_START_HERE.md` and
`02_CURRENT_STATE.md`. Run `bash scripts/project_doctor.sh` before planning —
it answers most environment questions in seconds.

## Correlation-id propagation — COMPLETE (verified 2026-09-05)

- `WorkflowRun` now carries an optional `correlation_id`; `WorkflowEngine.start`
  accepts/derives one and stamps it onto the run and its context,
  `WorkflowEngine.resume` re-injects it into context on every resume, the
  workflow `POST /run` API binds `request.state.correlation_id`, and
  `handlers.run_tool` forwards it into `ToolExecutor.execute`. A workflow's
  tool-step audit rows now share the same correlation id as the run.
- Runtime executions already carry it too: `RuntimeRequest`/`RuntimeExecution`
  (`app/runtime/models.py`) both declare `correlation_id`, the runtime API
  binds or generates one per call, and `RuntimeService` passes it through to
  the adapter. Nothing further is needed there.
- Verified: focused `tests/test_phase8_workflows.py` 28 passed; full
  `bash scripts/local_mac.sh test` — backend 369 passed / 5 skipped, frontend 109
  tests passed, typecheck/build clean, lint 0 errors / 9 pre-existing warnings.
- This closes the "thread the same correlation id through workflow runs"
  follow-on noted under section 2 below. Combined with the direct tool-call
  path (2026-08-31) and the runtime path (already in place), correlation-id
  propagation across the codebase is now complete — remaining work in this
  area is general observability (structured logs, timing, tenant placeholder),
  not correlation-id threading.
- Not deployed; no credential or hardware change involved.

## Local Mac operation (verified 2026-09-04)

- Start everything: `bash scripts/local_mac.sh start`
- Check health: `bash scripts/local_mac.sh status`
- Run all checks: `bash scripts/local_mac.sh test`
- Stop THYNACT-owned processes only: `bash scripts/local_mac.sh stop`
- Current local state is **LIVE_VALIDATED** with durable PostgreSQL/pgvector
  and Redis. Provider credentials remain optional and unset; the default LLM
  provider is `mock`.

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

## CONNECTOR PLATFORM — WHAT TO DO NEXT (updated 2026-09-04)

The active expansion goal is tracked in `PROJECT_BRAIN/11_CONNECTOR_ROADMAP.md`.
Telegram is now implemented/tested but credential-gated. Phase 1 continues
with WhatsApp Cloud, Instagram, and Teams; commerce
then starts with Shopify, Stripe, Amazon SP-API, and WooCommerce. Every entry
must pass the adapter/capability/approval/audit/test/live-validation contract;
the goal is not to inflate the catalog with unconnected cards.

The broker exists now, so wiring a provider operation is a small change
against a governed path rather than an architectural one: implement
`run_capability` on the adapter, and the risk, approval, routing and audit are
already there. `app/integrations/openai.py` is the worked example.



The capability layer, risk classification and SSRF guard are in
(`02_CURRENT_STATE.md`). Ordered by what actually unblocks the most:

1. **One real provider credential.** Nothing in this repository is
   LIVE_VALIDATED, and no amount of further engineering changes that — the
   environment has no API key and no OAuth client for any provider. A single
   OpenAI or Anthropic key, or one registered GitHub OAuth app, converts a
   whole column of CREDENTIAL_REQUIRED/AUTH_REQUIRED into a real governed call
   with an audit receipt. Start here.
2. **Credential vault.** OAuth access tokens live in **process memory**
   (`OAuthConnectionStore`) and are lost on restart. Encrypted persistence is
   the prerequisite for any connector surviving a deploy.
3. **Tenant model.** Not a connector feature — the precondition for one. See
   the multi-tenancy section of `02_CURRENT_STATE.md`; do not ship multi-user
   on the current store.
4. **Finish the four OAuth providers that already have full flows** (GitHub,
   GitLab, Slack, Notion) by mapping their canonical capabilities to real
   operations. Today each adapter only verifies identity; `repo.issue.create`
   and `chat.message.send` are declared but not wired.
5. **Then** expand to new providers, highest-value first (Gmail, Google
   Calendar, Google Drive, Telegram, Stripe). Discord now has a tested
   send-only adapter but still needs a real webhook URL for live validation.
   Each new provider needs the full loop, not a card: transport, capability mapping, credential, risk, approval,
   audit, test, real call. One finished connector beats ten declared ones.

Do **not** add catalog entries for providers without adapters. Fifteen already
sit at NOT_IMPLEMENTED; more would make the marketplace a list of things that
do not work.

## OPEN RIGHT NOW (2026-09-03)

**Production deploy of the About page + connector marketplace is pending.**
`claude/thynact-env-audit-fjinfj` is at `4cdc328`; `origin/main` is still at
`b429dc5`. The fast-forward was denied by the environment's permission
classifier, not by any code or test problem — everything is validated and
pushed. Merging `main` IS a production deploy on both Cloudflare Pages and
Render, so it needs the operator's go-ahead in this environment.

Not started from the 90-section marketplace/UX brief, in the order they are
worth doing:

1. **Custom connector wizard** — untrusted by default, unknown capabilities
   DENY, no plaintext secrets in localStorage / logs / PROJECT_BRAIN / audit
   payloads / git / connector metadata returned to the UI.
2. **AI provider management surface** — the catalog already carries Anthropic,
   Gemini and OpenAI entries; this is a management view over what exists, not
   a new registry.
3. **Backend security tests** for the connector paths.
4. **Privacy page long-form prose is still English only** — deliberate, and
   flagged for human legal review before it is translated.

## Manual actions only the operator can take

Everything else below can be done by an agent. Ranked — ask for **one** at a
time, highest first.

1. **Buy/choose the permanent THYNACT domain** (nine-point plan item 1). This is
   the top blocker: it gates stable production/staging URLs, permanent OAuth
   redirect and webhook callback URLs, and therefore every OAuth connector
   including Google. Until it exists, mark OAuth work `STABLE_DOMAIN_REQUIRED`
   and do not repeat the tunnel → callback → restart loop.
2. **RESOLVED IN PART (2026-09-02).** Production Postgres and Key Value are
   **provisioned** on Render's free plan via MCP — `dpg-dabo2bqfngtc73eogac0-a`
   (PostgreSQL 16, oregon, **expires 2026-10-02**) and
   `red-dabo2eifngtc73eoghkg` (Key Value 8.1.4, oregon,
   `persistenceMode: off`). Nothing billable was created.

   **The one remaining step is pasting `DATABASE_URL`** (and optionally
   `REDIS_URL`) into the production service's environment. The Render MCP
   exposes no connection string for either resource and env vars accept literal
   values only, so this specific step cannot be automated — see CLAUDE.md for
   the verified tool limits. Once it is set, run
   `uv run python scripts/cutover_preflight.py` before switching any
   `AGENT_OS_*_BACKEND`; it refuses a database that is unmigrated, missing
   pgvector, or stamped for the wrong environment.
3. Provide a scoped `AGENT_OS_API_KEY` value if authenticated live smoke tests
   against `api.thynact.com` are wanted.
4. Optional connector credentials, each unlocking exactly one connector:
   `GEMINI_API_KEY` (+ `AGENT_OS_LLM_PROVIDER=gemini`), `OPENAI_API_KEY`,
   `ANTHROPIC_API_KEY`, `CLOUDFLARE_API_TOKEN`, `RENDER_API_KEY`,
   `N8N_BASE_URL`, `MAKE_WEBHOOK_URL`, and the OAuth pairs for GitHub, GitLab,
   Slack and Notion.

## 0. CONSOLIDATED MANUAL-ACTION QUEUE

**DOMAIN BLOCKER RESOLVED — `thynact.com` is ACTIVE.** Do not label the project
`STABLE_DOMAIN_REQUIRED` any more; individual connectors may still be
`AUTH_REQUIRED` / `CREDENTIAL_REQUIRED` / `PROVIDER_APPROVAL_REQUIRED`.

Everything below needs a dashboard, a credential or a payment decision. This
session held no `CLOUDFLARE_API_TOKEN` / `RENDER_API_KEY`. Ordered by
dependency then value; never put secret values in this file.

1. **Render → create the free staging stack, branch `staging`.**
   `render.yaml` is now **all-free** (`plan: free` for web, Postgres and Key
   Value). The payment prompt was caused by the previous `plan: starter` (web)
   and `plan: basic-256mb` (Postgres) — both paid. **Do not add a payment
   method.**
   Try **New → Blueprint** first. If Blueprint still asks for a card (it has
   historically done so even for all-free specs), fall back to creating the
   three resources by hand — exact steps in `docs/DEPLOYMENT.md` §3b Path B.
   Same result, only the automation is lost.
   *Free-tier reality:* Postgres expires after 30 days, Key Value is in-memory
   only, the web service sleeps after 15 min idle, and 750 instance-hours/month
   are shared workspace-wide — check whether production is also free before
   running both.
   *Unlocks:* the entire staging environment, at zero cost.
2. **Render → `thynact-api-staging` → Custom domain → `api-staging.thynact.com`.**
   *Unlocks:* the staging frontend, which already routes there by hostname.
3. **Run migrations against staging once** — `AGENT_OS_APP_ENV=staging
   python scripts/migrate.py`. Expect `Environment: staging` then 7 applied.
   *Unlocks:* durable staging; the service will not boot until this is done,
   because `AGENT_OS_REQUIRE_DURABLE_PERSISTENCE=true`.
4. **Cloudflare Pages → `agent-os-test` → Custom domains → repoint
   `staging.thynact.com` to the `staging` branch** (it currently serves the
   production deployment — verified identical asset hash).
   *Unlocks:* a staging frontend that is actually staging.
5. **Render → production service → set `AGENT_OS_APP_ENV=production`.**
   Do this **before** any production database is attached so the stamp binds
   correctly. Safe, non-destructive, fixes the mislabelled `/health`.
6. **Provision production PostgreSQL (pgvector) + Redis** — paid
   infrastructure, needs explicit approval. Then follow the cutover sequence in
   `docs/DEPLOYMENT.md` §5 exactly; set
   `AGENT_OS_REQUIRE_DURABLE_PERSISTENCE=true` only at the end.
   *Unlocks:* production stops losing every task/workflow/approval/audit record
   on restart.
7. **Register per-environment OAuth apps** (GitHub first) with callbacks
   `https://api-staging.thynact.com/api/v1/integrations/oauth/{provider}/callback`
   and the `api.thynact.com` equivalent. Separate registrations per
   environment — see `docs/DEPLOYMENT.md` §4.
8. **Optional provider credentials**, one connector each: `GEMINI_API_KEY`,
   `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `CLOUDFLARE_API_TOKEN`,
   `RENDER_API_KEY`, `N8N_BASE_URL`, `MAKE_WEBHOOK_URL`.
9. **Production deployment authorization** — merging to `main` IS a production
   deploy. Withheld until staging is validated.

### Not needed from the operator
CI, lint, deploy-config validation, environment isolation, worker validation
and visual QA are all automated now. Cloudflare Access on preview URLs is
intentional security — do not weaken it; local rendering against the real local
backend is the engineering substitute, and is not a substitute for final
staging validation.

## 0b. Verified live state (2026-08-31)

| Host | State |
|---|---|
| `app.thynact.com` | Production frontend, Active + SSL |
| `staging.thynact.com` | **Still serving PRODUCTION** — identical asset hash. Not staging yet. |
| `api.thynact.com` | Live; `environment: development`, all backends `memory` |
| `api-staging.thynact.com` | Does not resolve |
| `staging.agent-os-test.pages.dev` | Branch preview exists, gated by Cloudflare Access |

**STAGING_READY: NO.** Frontend routing, backend isolation, durability guards,
deploy config and CI are implemented and tested; the staging backend does not
exist and `staging.thynact.com` still points at production.
**Do not merge to `main`.** `main` is untouched.

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
- **Postgres-backed correctness under real data.** Approval single-use
  semantics are now covered against real PostgreSQL, including two-way and
  ten-way concurrent consumption. Next, add targeted real-database coverage
  for memory hybrid ranking and workflow run resume.
- ~~Audit correlation-ID quick-copy~~ **DONE** (migration 006, verified
  against real PostgreSQL). ~~Thread the same correlation id through workflow
  runs~~ **DONE 2026-09-05** — `WorkflowRun.correlation_id`, engine
  start/resume, the workflow API, and tool-step handlers all propagate it now.
  Runtime executions already carried it (`RuntimeRequest`/`RuntimeExecution`,
  bound in the runtime API, forwarded by `RuntimeService`). Correlation-id
  propagation across the codebase is now **DONE** end to end.
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
