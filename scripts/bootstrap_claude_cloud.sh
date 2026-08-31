#!/usr/bin/env bash
# THYNACT — idempotent Claude cloud bootstrap.
#
# Safe to re-run: it never drops databases, never resets migrations, never
# deletes dependencies, and never writes secrets. Everything it does is either
# already-done (skipped) or additive.
#
# Usage:
#   bash scripts/bootstrap_claude_cloud.sh          # deps + services + migrations
#   SKIP_SERVICES=1 bash scripts/bootstrap_claude_cloud.sh   # deps only
#
# Local dev DSNs (never production credentials):
#   DATABASE_URL=postgresql://agent_os:agent_os_dev@127.0.0.1:5432/agent_os
#   REDIS_URL=redis://127.0.0.1:6379/0
set -uo pipefail
cd "$(dirname "$0")/.."

ok()   { printf '  \033[32mok\033[0m    %s\n' "$*"; }
skip() { printf '  \033[2m--\033[0m    %s\n' "$*"; }
warn() { printf '  \033[33mwarn\033[0m  %s\n' "$*"; }
fail() { printf '  \033[31mFAIL\033[0m  %s\n' "$*"; }
step() { printf '\n\033[1m%s\033[0m\n' "$*"; }

FAILED=0

step "1. Python toolchain"
if ! command -v uv >/dev/null 2>&1; then
  fail "uv not installed — install from https://docs.astral.sh/uv/ then re-run"
  exit 1
fi
ok "uv $(uv --version | awk '{print $2}')"
# The project needs >=3.12; the sandbox default python3 is often 3.11. uv binds
# the right interpreter itself, so never invoke bare python/pytest for project work.
if [ -x .venv/bin/python ] && .venv/bin/python -c "import fastapi" 2>/dev/null; then
  skip "python deps already synced ($(.venv/bin/python -V 2>&1))"
else
  # --frozen: use uv.lock as-is, never re-lock as a side effect of setup.
  if uv sync --extra dev --frozen >/dev/null 2>&1; then
    ok "python deps synced ($(.venv/bin/python -V 2>&1))"
  else
    fail "uv sync failed — re-run manually: uv sync --extra dev --frozen"; FAILED=1
  fi
fi

step "2. Frontend toolchain"
if ! command -v pnpm >/dev/null 2>&1; then
  warn "pnpm not found — frontend work unavailable (corepack enable pnpm)"
elif [ -d frontend/node_modules ]; then
  skip "frontend deps already installed"
else
  if (cd frontend && pnpm install --frozen-lockfile >/dev/null 2>&1); then
    ok "frontend deps installed"
  else
    fail "pnpm install failed — re-run manually in frontend/"; FAILED=1
  fi
fi

if [ "${SKIP_SERVICES:-0}" = "1" ]; then
  step "3-5. Services skipped (SKIP_SERVICES=1)"
else

step "3. PostgreSQL + pgvector"
if ! command -v pg_ctlcluster >/dev/null 2>&1; then
  warn "no native PostgreSQL — skipping (durable backends will stay 'memory')"
else
  if pg_isready -q 2>/dev/null; then
    skip "postgres already running"
  elif pg_ctlcluster 16 main start 2>/dev/null && pg_isready -q 2>/dev/null; then
    ok "postgres started"
  else
    fail "could not start postgres"; FAILED=1
  fi

  if pg_isready -q 2>/dev/null; then
    # pgvector is a hard requirement: migrations 001/002 CREATE EXTENSION vector,
    # use vector columns and build an HNSW index. Without it migrations abort.
    if ls /usr/share/postgresql/16/extension/vector.control >/dev/null 2>&1; then
      skip "pgvector package present"
    else
      warn "pgvector missing — installing postgresql-16-pgvector"
      apt-get update -q >/dev/null 2>&1
      if apt-get install -y -q postgresql-16-pgvector >/dev/null 2>&1; then
        ok "pgvector installed"
      else
        fail "pgvector install failed — migrations will not apply"; FAILED=1
      fi
    fi

    # Development-local role/database only. Never touched if already present.
    if ! su postgres -c "psql -tAc \"SELECT 1 FROM pg_roles WHERE rolname='agent_os'\"" 2>/dev/null | grep -q 1; then
      su postgres -c "psql -qc \"CREATE ROLE agent_os LOGIN PASSWORD 'agent_os_dev';\"" >/dev/null 2>&1 \
        && ok "dev role agent_os created" || { fail "could not create dev role"; FAILED=1; }
    else
      skip "dev role agent_os exists"
    fi
    if ! su postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='agent_os'\"" 2>/dev/null | grep -q 1; then
      su postgres -c "createdb -O agent_os agent_os" >/dev/null 2>&1 \
        && ok "dev database agent_os created" || { fail "could not create dev database"; FAILED=1; }
    else
      skip "dev database agent_os exists"
    fi
    su postgres -c "psql -d agent_os -qc 'CREATE EXTENSION IF NOT EXISTS vector;'" >/dev/null 2>&1 \
      && ok "vector extension enabled" || warn "could not enable vector extension"
  fi
fi

step "4. Redis"
if ! command -v redis-server >/dev/null 2>&1; then
  warn "no native Redis — skipping (queue backend will stay 'memory')"
elif redis-cli ping >/dev/null 2>&1; then
  skip "redis already running"
else
  redis-server /etc/redis/redis.conf --daemonize yes --save '' --appendonly no >/dev/null 2>&1
  sleep 1
  redis-cli ping >/dev/null 2>&1 && ok "redis started" || { fail "could not start redis"; FAILED=1; }
fi

step "5. Migrations"
# Idempotent by design: run_migrations tracks applied files in schema_migrations
# under an advisory lock. It is never destructive; re-running is a no-op.
if pg_isready -q 2>/dev/null && [ -x .venv/bin/python ]; then
  export DATABASE_URL="${DATABASE_URL:-postgresql://agent_os:agent_os_dev@127.0.0.1:5432/agent_os}"
  OUT=$(uv run python scripts/migrate.py 2>&1)
  if [ $? -eq 0 ]; then ok "$OUT"; else fail "migrations failed: $(echo "$OUT" | tail -2)"; FAILED=1; fi
else
  skip "migrations (postgres or python deps unavailable)"
fi

fi  # SKIP_SERVICES

step "6. Browser (visual QA)"
if [ -n "${THYNACT_CHROMIUM_EXECUTABLE:-}" ] && [ -x "${THYNACT_CHROMIUM_EXECUTABLE}" ]; then
  ok "chromium via THYNACT_CHROMIUM_EXECUTABLE"
elif [ -n "${PLAYWRIGHT_BROWSERS_PATH:-}" ] && [ -e "${PLAYWRIGHT_BROWSERS_PATH}/chromium" ]; then
  ok "chromium via PLAYWRIGHT_BROWSERS_PATH ($PLAYWRIGHT_BROWSERS_PATH)"
elif [ -d frontend/node_modules/playwright ]; then
  ok "playwright package present (managed browser resolved at launch)"
else
  warn "no chromium detected — pnpm screenshot will report what it tried"
fi

printf '\n'
if [ "$FAILED" = "0" ]; then
  printf '\033[32mBootstrap complete.\033[0m Next: bash scripts/project_doctor.sh\n'
else
  printf '\033[31mBootstrap finished with failures (see FAIL lines above).\033[0m\n'
fi
exit "$FAILED"
