# Production durability — persistence matrix and cutover

Verified against the code at the commit that introduced this file, and against
a real local PostgreSQL 16 + pgvector 0.6.0 and Redis 7. Every variable name
below was read out of `app/core/config.py`, not assumed.

## 1. Live production state (measured, not reported)

`curl https://api.thynact.com/health` currently returns:

```
environment  : development     <- AGENT_OS_APP_ENV is unset, so the default applies
persistence  : ephemeral
backends     : all seven "memory"
warnings     : []              <- suppressed ONLY because app_env is not production-like
```

Consequences, all of them current:

- Every task, workflow run, workflow definition, runtime execution, approval,
  audit event and memory record is lost on each restart and each redeploy.
- `/docs`, `/redoc` and `/openapi.json` are publicly served, because
  `settings.docs_enabled` is `app_env != "production"`. The code already closes
  them in production; nothing else is needed but the variable.
- `persistence_warnings()` stays silent because it only fires when
  `app_env in {production, staging}`. Production is not *pretending* to be
  durable — but it is not warning either, because it does not know it is
  production.

## 2. Persistence matrix

| Component | Current production backend | Expected durable backend | Env variable | Restart-safe today |
|---|---|---|---|---|
| Semantic memory | `memory` | `postgres_pgvector` | `AGENT_OS_MEMORY_BACKEND` | No |
| Tasks | `memory` | `postgres` | `AGENT_OS_TASK_BACKEND` | No |
| Workflow runs | `memory` | `postgres` | `AGENT_OS_WORKFLOW_BACKEND` | No |
| Workflow definitions | `memory` | `postgres` | `AGENT_OS_WORKFLOW_DEFINITION_BACKEND` | No |
| Runtime executions | `memory` | `postgres` | `AGENT_OS_RUNTIME_BACKEND` | No |
| Tool approvals + audit | `memory` | `postgres` | `AGENT_OS_TOOL_BACKEND` | No |
| Job queue | `memory` | `redis` | `AGENT_OS_QUEUE_BACKEND` | No |
| PostgreSQL connection | — | required by all `postgres*` values | `DATABASE_URL` | — |
| Redis connection | — | required by `redis` queue | `REDIS_URL` | — |

Accepted values are exact: `memory` \| `postgres` for every store,
`memory` \| `postgres` \| `postgres_pgvector` for memory, and
`memory` \| `redis` for the queue. Anything else falls through to the in-memory
branch.

### Not covered by any store — ephemeral even with a database attached

These live in process-local dictionaries (`app/runtime/circuit_breaker.py`,
`app/runtime/rate_limit.py`, `app/runtime/store.py`) and have **no** durable
implementation today:

- circuit-breaker state
- sliding-window rate-limit counters
- idempotency keys held in the runtime store's in-memory index

They reset on restart even in a fully configured deployment. That is a known
limitation, recorded here so nobody reads the matrix above and concludes the
whole runtime is durable.

## 3. Fail-closed behaviour

`AGENT_OS_REQUIRE_DURABLE_PERSISTENCE=true` makes the API refuse to start when
any subsystem is still in-memory (`app/main.py` lifespan), and makes `/ready`
answer 503. It is opt-in rather than implied by `app_env` on purpose: turning it
on implicitly for production would convert today's silent degradation into an
immediate outage for a service that has no `DATABASE_URL` yet.

**Set it only AFTER the database and Redis are attached and migrations have
run.** It is the last step of the cutover, not the first.

## 4. Environment stamp

`migrations/007` writes the environment into `deployment_environment`, and
`app/persistence/environment.py` refuses to run against a database stamped for a
different environment. `scripts/migrate.py` checks this *before* touching schema
and exits 1 on mismatch — verified locally: a `production` app against a
`development` database refused and exited 1.

## 5. Redis namespacing

All queue keys are built by `RedisJobQueue._key()` from `settings.queue_namespace`
= `{AGENT_OS_QUEUE_PREFIX}:{AGENT_OS_APP_ENV}`, e.g. `agent-os:production`.
There is exactly one Redis client construction site in the codebase, so there is
no path that bypasses the namespace. The constructor's `prefix` argument is
required (it previously defaulted to the bare, environment-less `agent-os`).

**Because the namespace embeds `AGENT_OS_APP_ENV`, a production service running
with the default `development` value would read and write `agent-os:development`
keys.** That is a second reason the environment variable must be set before
Redis is attached.

## 6. Cutover procedure

Ordering matters. Steps 1-2 are safe at any time; step 6 is the only one that
can take the service down if performed early.

1. **Set `AGENT_OS_APP_ENV=production`** on the Render API service.
   Immediately: `/docs`, `/redoc`, `/openapi.json` close; `/health` reports
   `environment: production` and starts emitting the ephemeral-storage warning;
   the Redis namespace becomes `agent-os:production`. Nothing goes down —
   `/ready` still answers 200 while degraded, by design.
2. **Provision PostgreSQL** and set `DATABASE_URL`. Provision Redis / Render Key
   Value and set `REDIS_URL` if the queue is wanted.
3. **Run migrations** against the production database:
   `uv run python scripts/migrate.py` (the Docker image ships `migrations/` and
   `scripts/` and installs the `persistence` extra, so this is runnable
   in-container). It stamps the database `production` and refuses to run if
   `AGENT_OS_APP_ENV` disagrees.
4. **Switch the backends**: `AGENT_OS_MEMORY_BACKEND=postgres_pgvector`,
   `AGENT_OS_TASK_BACKEND`/`WORKFLOW`/`WORKFLOW_DEFINITION`/`RUNTIME`/`TOOL` =
   `postgres`, `AGENT_OS_QUEUE_BACKEND=redis`.
5. **Redeploy** and verify: `/live` 200; `/health` shows
   `persistence: durable` and no memory backends; `/ready` 200 with
   `status: ready` and `database: ok`, `queue: ok`.
6. **Set `AGENT_OS_REQUIRE_DURABLE_PERSISTENCE=true`** last, to fail closed from
   then on.
7. **Prove durability for real**: create a task, redeploy the service, read the
   task back. Until that passes against Render, durability is
   `LOCAL_REAL_VALIDATED`, not `PRODUCTION_VALIDATED`.

## 7. pgvector

`migrations/001` and `002` run `CREATE EXTENSION vector` and build an HNSW
index. That requires an extension-creating role. Render's managed PostgreSQL
allows `CREATE EXTENSION vector`; if the role cannot, migration 001 fails and
the memory backend cannot be `postgres_pgvector`. Confirm this before step 4.
