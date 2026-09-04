#!/usr/bin/env bash
# THYNACT-only macOS development stack. Uses dedicated data directories and ports.
set -euo pipefail

cd "$(dirname "$0")/.."

ROOT="$PWD"
STATE="$ROOT/.thynact-local"
PGDATA="$STATE/postgres"
PGPORT="${THYNACT_PGPORT:-55432}"
REDIS_PORT="${THYNACT_REDIS_PORT:-56379}"
API_PORT="${THYNACT_API_PORT:-8000}"
WEB_PORT="${THYNACT_WEB_PORT:-3000}"
SESSION="thynact"
PNPM="/opt/homebrew/opt/node@20/bin/corepack pnpm@10.26.1"

export PATH="/opt/homebrew/opt/node@20/bin:/opt/homebrew/opt/postgresql@16/bin:/opt/homebrew/opt/redis/bin:$PATH"
export DATABASE_URL="postgresql://agent_os:agent_os_dev@127.0.0.1:${PGPORT}/agent_os"
export REDIS_URL="redis://127.0.0.1:${REDIS_PORT}/0"
export AGENT_OS_MEMORY_BACKEND=postgres
export AGENT_OS_TASK_BACKEND=postgres
export AGENT_OS_WORKFLOW_BACKEND=postgres
export AGENT_OS_WORKFLOW_DEFINITION_BACKEND=postgres
export AGENT_OS_RUNTIME_BACKEND=postgres
export AGENT_OS_TOOL_BACKEND=postgres
export AGENT_OS_QUEUE_BACKEND=redis

usage() { echo "Usage: bash scripts/local_mac.sh setup|start|status|stop|test|shell-env"; }
port_free() { ! lsof -nP -iTCP:"$1" -sTCP:LISTEN >/dev/null 2>&1; }

setup() {
  mkdir -p "$STATE"
  if [ ! -s "$PGDATA/PG_VERSION" ]; then
    initdb -D "$PGDATA" --username=agent_os --auth-local=trust --auth-host=scram-sha-256 >/dev/null
    printf "listen_addresses = '127.0.0.1'\nport = %s\n" "$PGPORT" >> "$PGDATA/postgresql.conf"
  fi
  if ! pg_ctl -D "$PGDATA" status >/dev/null 2>&1; then
    port_free "$PGPORT" || { echo "FAIL: port $PGPORT is already in use"; exit 1; }
    pg_ctl -D "$PGDATA" -l "$STATE/postgres.log" start >/dev/null
  fi
  # The cluster's local socket uses trust authentication only for this initial
  # role/database setup; TCP is SCRAM-protected from the first connection.
  if ! psql -p "$PGPORT" -U agent_os -d postgres -tAc "SELECT 1 FROM pg_database WHERE datname='agent_os'" | grep -q 1; then
    createdb -p "$PGPORT" -U agent_os agent_os
  fi
  psql -p "$PGPORT" -U agent_os -d postgres -c "ALTER ROLE agent_os PASSWORD 'agent_os_dev'" >/dev/null
  PGPASSWORD=agent_os_dev psql -h 127.0.0.1 -p "$PGPORT" -U agent_os -d agent_os -c "CREATE EXTENSION IF NOT EXISTS vector" >/dev/null
  if ! redis-cli -p "$REDIS_PORT" ping >/dev/null 2>&1; then
    port_free "$REDIS_PORT" || { echo "FAIL: port $REDIS_PORT is already in use"; exit 1; }
    redis-server --bind 127.0.0.1 --port "$REDIS_PORT" --dir "$STATE" --dbfilename redis.rdb --daemonize yes --pidfile "$STATE/redis.pid" --logfile "$STATE/redis.log"
  fi
  uv sync --extra dev --frozen
  (cd frontend && CI=true $PNPM install --frozen-lockfile)
  uv run python scripts/migrate.py
  echo "THYNACT local dependencies and isolated services are ready."
}

start() {
  setup
  if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "THYNACT is already running in tmux session '$SESSION'."
    exit 0
  fi
  port_free "$API_PORT" || { echo "FAIL: API port $API_PORT is already in use"; exit 1; }
  port_free "$WEB_PORT" || { echo "FAIL: web port $WEB_PORT is already in use"; exit 1; }
  tmux new-session -d -s "$SESSION" -n api "cd '$ROOT' && source <(bash scripts/local_mac.sh shell-env) && uv run uvicorn app.main:app --reload --port '$API_PORT'"
  tmux new-window -t "$SESSION" -n web "cd '$ROOT/frontend' && PATH='/opt/homebrew/opt/node@20/bin:/usr/bin:/bin' /opt/homebrew/opt/node@20/bin/corepack pnpm@10.26.1 dev --host 127.0.0.1 --port '$WEB_PORT'"
  echo "THYNACT started: http://127.0.0.1:$WEB_PORT (tmux session '$SESSION')."
}

status() {
  pg_isready -h 127.0.0.1 -p "$PGPORT" || true
  redis-cli -p "$REDIS_PORT" ping || true
  curl -fsS --max-time 2 "http://127.0.0.1:${API_PORT}/health" || true
  echo
  tmux list-windows -t "$SESSION" 2>/dev/null || echo "Application session not running."
}

stop() {
  tmux kill-session -t "$SESSION" 2>/dev/null || true
  if [ -f "$STATE/redis.pid" ]; then
    pid="$(cat "$STATE/redis.pid")"
    command_line="$(ps -p "$pid" -o command= 2>/dev/null || true)"
    if [[ "$command_line" == *redis-server* && "$command_line" == *":${REDIS_PORT}"* ]]; then
      kill "$pid" 2>/dev/null || true
    else
      echo "WARN: refused to stop unverified process from $STATE/redis.pid"
    fi
  fi
  pg_ctl -D "$PGDATA" stop -m fast >/dev/null 2>&1 || true
  echo "Stopped THYNACT-owned processes only."
}

test_all() {
  (
    unset DATABASE_URL REDIS_URL AGENT_OS_MEMORY_BACKEND AGENT_OS_TASK_BACKEND
    unset AGENT_OS_WORKFLOW_BACKEND AGENT_OS_WORKFLOW_DEFINITION_BACKEND
    unset AGENT_OS_RUNTIME_BACKEND AGENT_OS_TOOL_BACKEND AGENT_OS_QUEUE_BACKEND
    uv run pytest tests/ -q
  )
  (cd frontend && $PNPM typecheck && $PNPM lint && $PNPM test && $PNPM build)
}

shell_env() {
  printf 'export PATH=%q\n' "$PATH"
  for name in DATABASE_URL REDIS_URL AGENT_OS_MEMORY_BACKEND AGENT_OS_TASK_BACKEND AGENT_OS_WORKFLOW_BACKEND AGENT_OS_WORKFLOW_DEFINITION_BACKEND AGENT_OS_RUNTIME_BACKEND AGENT_OS_TOOL_BACKEND AGENT_OS_QUEUE_BACKEND; do
    printf 'export %s=%q\n' "$name" "${!name}"
  done
}

case "${1:-}" in
  setup) setup ;;
  start) start ;;
  status) status ;;
  stop) stop ;;
  test) test_all ;;
  shell-env) shell_env ;;
  *) usage; exit 2 ;;
esac
