#!/usr/bin/env bash
# THYNACT — environment diagnostics. REPORTS ONLY, changes nothing.
#
# Exists so a fresh session does not spend 15 minutes rediscovering the
# environment. To actually fix what this reports, run:
#   bash scripts/bootstrap_claude_cloud.sh
#
# Never prints secret VALUES — only whether a name is set.
set -uo pipefail
cd "$(dirname "$0")/.."

row()  { printf '  %-22s %s\n' "$1" "$2"; }
good() { printf '  %-22s \033[32m%s\033[0m\n' "$1" "$2"; }
bad()  { printf '  %-22s \033[31m%s\033[0m\n' "$1" "$2"; }
soft() { printf '  %-22s \033[33m%s\033[0m\n' "$1" "$2"; }
head_() { printf '\n\033[1m%s\033[0m\n' "$*"; }

head_ "Repository"
row "branch" "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || echo '?')"
row "head" "$(git log --oneline -1 2>/dev/null || echo '?')"
DIRTY=$(git status --short 2>/dev/null | wc -l)
[ "$DIRTY" = "0" ] && good "working tree" "clean" || soft "working tree" "$DIRTY changed file(s)"

head_ "Python"
command -v uv >/dev/null 2>&1 && good "uv" "$(uv --version | awk '{print $2}')" || bad "uv" "MISSING"
if [ -x .venv/bin/python ]; then
  good "venv" "$(.venv/bin/python -V 2>&1 | awk '{print $2}')"
  .venv/bin/python -c "import fastapi" 2>/dev/null && good "backend deps" "installed" || bad "backend deps" "MISSING (uv sync --extra dev --frozen)"
  .venv/bin/python -c "import asyncpg, redis" 2>/dev/null && good "asyncpg/redis" "installed" || soft "asyncpg/redis" "missing (persistence extra)"
else
  bad "venv" "MISSING (uv sync --extra dev --frozen)"
fi
row "system python3" "$(python3 -V 2>&1 | awk '{print $2}') (project needs >=3.12 — use uv run)"

head_ "Frontend"
command -v node >/dev/null 2>&1 && good "node" "$(node -v)" || bad "node" "MISSING"
command -v pnpm >/dev/null 2>&1 && good "pnpm" "$(pnpm --version)" || bad "pnpm" "MISSING"
row "pinned node" "$(cat frontend/.node-version 2>/dev/null || echo '?') (Cloudflare build)"
[ -d frontend/node_modules ] && good "frontend deps" "installed" || bad "frontend deps" "MISSING (pnpm install --frozen-lockfile)"

head_ "Docker"
if [ -S /var/run/docker.sock ]; then
  good "daemon" "reachable"
else
  soft "daemon" "absent — use native postgres/redis (infra/ compose is for other envs)"
fi

head_ "PostgreSQL"
if command -v pg_isready >/dev/null 2>&1 && pg_isready -q 2>/dev/null; then
  good "server" "running ($(psql --version | awk '{print $3}'))"
  if ls /usr/share/postgresql/*/extension/vector.control >/dev/null 2>&1; then
    good "pgvector pkg" "installed"
  else
    bad "pgvector pkg" "MISSING (apt-get install postgresql-16-pgvector) — migrations will fail"
  fi
  if su postgres -c "psql -tAc \"SELECT 1 FROM pg_database WHERE datname='agent_os'\"" 2>/dev/null | grep -q 1; then
    good "dev database" "agent_os exists"
    EXT=$(su postgres -c "psql -d agent_os -tAc \"SELECT extversion FROM pg_extension WHERE extname='vector'\"" 2>/dev/null | tr -d ' ')
    [ -n "$EXT" ] && good "vector extension" "enabled (v$EXT)" || bad "vector extension" "not enabled in agent_os"
    APPLIED=$(su postgres -c "psql -d agent_os -tAc 'SELECT count(*) FROM schema_migrations'" 2>/dev/null | tr -d ' ')
    ONDISK=$(ls migrations/*.sql 2>/dev/null | wc -l | tr -d ' ')
    if [ -n "$APPLIED" ]; then
      [ "$APPLIED" = "$ONDISK" ] && good "migrations" "$APPLIED/$ONDISK applied" || soft "migrations" "$APPLIED/$ONDISK applied (run scripts/migrate.py)"
    else
      soft "migrations" "0/$ONDISK applied (run scripts/migrate.py)"
    fi
  else
    soft "dev database" "agent_os absent (bootstrap creates it)"
  fi
else
  soft "server" "not running (pg_ctlcluster 16 main start)"
fi

head_ "Redis"
if command -v redis-cli >/dev/null 2>&1 && redis-cli ping >/dev/null 2>&1; then
  good "server" "running ($(redis-server --version | sed 's/.*v=\([0-9.]*\).*/\1/'))"
else
  soft "server" "not running (redis-server /etc/redis/redis.conf --daemonize yes)"
fi

head_ "Browser (visual QA)"
if [ -n "${THYNACT_CHROMIUM_EXECUTABLE:-}" ] && [ -x "${THYNACT_CHROMIUM_EXECUTABLE}" ]; then
  good "chromium" "THYNACT_CHROMIUM_EXECUTABLE"
elif [ -n "${PLAYWRIGHT_BROWSERS_PATH:-}" ] && [ -e "${PLAYWRIGHT_BROWSERS_PATH}/chromium" ]; then
  good "chromium" "$PLAYWRIGHT_BROWSERS_PATH/chromium"
elif [ -d frontend/node_modules/playwright ]; then
  good "chromium" "playwright-managed (resolved at launch)"
else
  soft "chromium" "none detected — pnpm screenshot reports what it tried"
fi

head_ "Application health (only if running locally)"
if curl -sS --max-time 2 http://127.0.0.1:8000/health >/dev/null 2>&1; then
  good "api /health" "$(curl -sS --max-time 2 http://127.0.0.1:8000/health | head -c 200)"
  row "api /ready" "$(curl -sS --max-time 2 http://127.0.0.1:8000/ready | head -c 160)"
else
  soft "api" "not running on :8000 (uv run uvicorn app.main:app)"
fi
curl -sS --max-time 2 -o /dev/null http://127.0.0.1:3000/ 2>/dev/null \
  && good "frontend dev" "running on :3000" || soft "frontend dev" "not running (cd frontend && pnpm dev)"

head_ "Credential presence (names only — values never printed)"
for v in AGENT_OS_API_KEY DATABASE_URL REDIS_URL GEMINI_API_KEY OPENAI_API_KEY \
         ANTHROPIC_API_KEY CLOUDFLARE_API_TOKEN RENDER_API_KEY N8N_BASE_URL \
         GITHUB_OAUTH_CLIENT_ID GITHUB_OAUTH_CLIENT_SECRET; do
  if [ -n "${!v:-}" ]; then good "$v" "set"; else row "$v" "not set"; fi
done

printf '\n\033[2mReport only — nothing was changed. To fix: bash scripts/bootstrap_claude_cloud.sh\033[0m\n'
