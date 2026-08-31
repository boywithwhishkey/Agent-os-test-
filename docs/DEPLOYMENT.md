# THYNACT — Deployment, Environments and Recovery

Operational reference. Durable rules live in root `CLAUDE.md`; changing state
lives in `PROJECT_BRAIN/`. Everything here was verified against the repository
or a real local PostgreSQL/Redis on 2026-08-31 — claims that were **not**
verified are labelled as such.

Permanent domain: **thynact.com** (ACTIVE).

## 1. Environment map

| | Frontend | Backend | Branch | Datastores |
|---|---|---|---|---|
| Production | `app.thynact.com` | `api.thynact.com` | `main` | none yet — **ephemeral** |
| Staging | `staging.thynact.com` | `api-staging.thynact.com` | `staging` | own Postgres + own Redis |
| Preview | `*.agent-os-test.pages.dev` | staging API | any other branch | staging's |

Cloudflare Pages project: `agent-os-test`. Backend: Render.
**Never point `api.thynact.com` at Cloudflare Pages** — it is the Render host.
Preview URLs are protected by Cloudflare Access; that is intentional security,
not a bug, and must not be weakened to make automation easier.

## 2. How isolation is enforced (code, not convention)

1. **API host is derived from the served hostname** —
   `frontend/src/lib/api/config.ts` and `functions/api/v1/orchestrate.js`.
   Only `app.thynact.com` resolves to the production API; staging, previews
   and any unexpected host fall back to staging. Never reintroduce a hardcoded
   production URL as a default.
2. **Database environment stamp** — `migrations/007` stamps a database with the
   environment that first used it; `app/persistence/environment.py` refuses to
   proceed on mismatch, and `scripts/migrate.py` checks *before* touching schema
   and exits 1. Verified: a `development`-stamped database is accepted as
   `development` and refused for both `production` and `staging`.
3. **Redis namespace** — `settings.queue_namespace` is `agent-os:<env>`. Proven
   against a real broker: two queues on one Redis with the same logical queue
   name do not see each other's jobs.
4. **Environment label in the UI** — non-production deployments show a badge.
5. **`AGENT_OS_APP_ENV` is validated** against production/staging/development/
   test, so a typo cannot invent a fourth environment.

## 3. Staging secret / configuration contract

Set in the Render dashboard on `thynact-api-staging`. **Names only — never
commit values.** Staging values must differ from production.

| Variable | Class | Notes |
|---|---|---|
| `AGENT_OS_APP_ENV` | non-secret config | `staging`. Must match the DB stamp. |
| `AGENT_OS_API_KEY` | **required secret** | Operator key gating `/api/v1/*`. Generate a fresh one; never reuse production's. |
| `DATABASE_URL` | derived | Injected from `thynact-staging-db`. Never a literal. |
| `REDIS_URL` | derived | Injected from `thynact-staging-redis`. Never a literal. |
| `AGENT_OS_REQUIRE_DURABLE_PERSISTENCE` | non-secret config | `true` — fail closed if any subsystem is still in-memory. |
| `AGENT_OS_*_BACKEND` (6) | non-secret config | `postgres`; queue is `redis`. |
| `AGENT_OS_CORS_ORIGINS` | non-secret config | `https://staging.thynact.com` only. |
| `AGENT_OS_FRONTEND_URL` | non-secret config | `https://staging.thynact.com`. |
| `AGENT_OS_OAUTH_REDIRECT_BASE_URL` | non-secret config | `https://api-staging.thynact.com`. |
| `GITHUB_OAUTH_CLIENT_ID` / `_SECRET` | OAuth credential | **Separate app registration**, not production's with another callback. |
| `GEMINI_API_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `CLOUDFLARE_API_TOKEN`, `RENDER_API_KEY`, `N8N_BASE_URL`, `MAKE_WEBHOOK_URL` | optional provider credentials | Leave unset. Each then reports `CREDENTIAL_REQUIRED` honestly instead of borrowing production credentials. |

There is **no** session/cookie secret and **no** credential-encryption key in
this codebase today: the operator key is sent as `X-API-Key` and held in the
browser's `sessionStorage`, and OAuth access tokens live in process memory
(`app/integrations/oauth/store.py`), never persisted. Persisting them later
requires encryption at rest and a key-management decision — see §7.

## 4. OAuth callback architecture

Four providers are implemented (`app/integrations/oauth/config.py`):
GitHub, Slack, Notion, GitLab. Callback route:

```
{AGENT_OS_OAUTH_REDIRECT_BASE_URL}/api/v1/integrations/oauth/{provider}/callback
```

so production is `https://api.thynact.com/...` and staging
`https://api-staging.thynact.com/...`. Register **both** with each provider, or
register separate apps per environment (preferred, and required where a
provider allows only one callback).

| Provider | Scope | Token auth | Notes |
|---|---|---|---|
| GitHub | `repo read:org` | form | Reference implementation |
| Slack | `chat:write channels:read` | form | Always returns HTTP 200; errors appear as `{"ok": false}` in the body |
| Notion | *(none)* | basic | No scope param; capabilities chosen when the integration is created |
| GitLab | `read_api read_user` | form | |

**Not implemented, honestly:** PKCE (no `code_challenge` anywhere), refresh-token
rotation, and revocation. CSRF is handled by a single-use, TTL'd state token.
Tokens are in-memory only, so every backend restart drops OAuth connections —
acceptable for staging validation, not for production use.

## 5. Production durability cutover plan (NOT executed)

Production today: `environment: development`, all seven subsystems on `memory`.
Every task, workflow, approval and audit record is lost on each restart or
redeploy. Sequence to fix, in order:

1. Provision production Postgres (**pgvector required**) and Redis. Paid
   infrastructure — needs explicit approval.
2. Set `AGENT_OS_APP_ENV=production` on the Render service **first**, before any
   database is attached, so the stamp binds correctly on first migration.
3. Set `DATABASE_URL` / `REDIS_URL`.
4. Run `python scripts/migrate.py` **manually** — nothing runs it automatically.
   Confirm it prints `Environment: production`.
5. Flip the six `AGENT_OS_*_BACKEND` vars to `postgres` and the queue to `redis`.
6. Only then set `AGENT_OS_REQUIRE_DURABLE_PERSISTENCE=true`. Setting it earlier
   makes the service refuse to boot.
7. Verify `/health` shows `persistence: durable` with an empty `warnings`, and
   `/ready` returns real `database`/`queue` checks.

Rollback: unset the backend variables to fall back to memory. Data written to
Postgres is retained, but in-flight memory state is not migrated either way —
prefer a low-traffic window. There is currently **no data to migrate**, since
production has never had durable storage, which makes this cutover unusually
cheap. Do it before real users exist.

**Verify on first migration:** `CREATE EXTENSION vector` needs a role permitted
to create extensions. This failed locally with *"permission denied to create
extension / must be superuser"* until the role was granted it. If migration 001
fails that way on Render, the database user needs the privilege or an admin must
pre-create the extension.

## 6. Backups and recovery — PREPARED, NOT VALIDATED

No backups exist, because no production datastore exists. What will need it:

- **PostgreSQL** — the system of record: tasks, workflows and definitions,
  runtime executions, approvals, tool audit events, semantic memory (with
  embeddings), and the `deployment_environment` stamp.
- **Redis** — queue state only. Rebuildable; treat as recoverable, not backed up.
- **Deployment configuration** — `render.yaml` is in git; dashboard-managed
  production settings and all secrets are not, and must be recorded in a
  password manager.

Recovery procedure to run once infrastructure exists (**never yet executed**):

1. Take a snapshot/`pg_dump` of the source database.
2. Restore into an **isolated** database — never over a live one.
3. Run `scripts/migrate.py` against the restore with the matching
   `AGENT_OS_APP_ENV`. The stamp guard will refuse a mismatched restore, which
   is the desired behaviour: relabel deliberately rather than by accident.
4. Integrity checks: row counts per table, `SELECT extversion FROM pg_extension
   WHERE extname='vector'`, and the HNSW index present.
5. Boot the app against the restore and confirm `/ready` reports
   `database: ok`, `queue: ok`.
6. Sample verification: a known task, a memory search returning real scores, and
   an audit event with its correlation id.

**Duplicate-action risk after restore:** restoring a queue snapshot can re-run
jobs that already ran. Prefer restoring Postgres only and letting the queue
drain empty. Approvals are single-use and audit rows are append-only, which
limits but does not eliminate this.

RPO/RTO are **not yet set** — they are a business decision, not an engineering
one, and should be agreed before public beta. DR cannot be called ready until a
restore has actually been exercised.

## 7. Known gaps (do not describe these as done)

- No production datastores; production is ephemeral and mislabelled.
- No staging deployment yet — `render.yaml` has never been synced, so it is
  unvalidated against Render's live schema.
- OAuth tokens are in-memory and unencrypted; no vault, no rotation.
- No scheduler subsystem exists (a `JobWorker` does; a scheduler does not).
- No external metrics/tracing/alerting stack.
- No multi-tenancy: there is no tenant column or principal beyond the single
  operator API key. Tenant isolation is a design goal, not a current property.
- No rate limiting on the public API surface (the runtime rate limiter governs
  integration calls, not inbound HTTP). Verified: no inbound limiter exists.
- No request size limits or explicit request timeouts on inbound HTTP.

Closed in this pass: security headers (`X-Content-Type-Options`,
`X-Frame-Options`, `Referrer-Policy`) are now set on every response, and
`/docs`, `/redoc` and `/openapi.json` are disabled when
`AGENT_OS_APP_ENV=production` unless `AGENT_OS_ENABLE_DOCS` re-enables them —
previously the full route surface was published anonymously from a public
hostname.
