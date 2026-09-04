#!/usr/bin/env bash
# THYNACT — the full local gate. Runs everything CI runs, against the real
# local PostgreSQL and Redis, and reports one pass/fail.
#
# This is the "is my working tree actually good?" command. It is deliberately
# NOT a deploy command and never will be: local verification and production
# release stay separate so that neither can happen by accident. Nothing here
# pushes, merges, deploys, or writes to any remote.
#
# Non-destructive: no migration is rolled back, no table dropped, no database
# reset. Migrations are idempotent by design and re-running them is a no-op.
#
#   bash scripts/verify_local.sh          # everything
#   bash scripts/verify_local.sh backend  # backend only
#   bash scripts/verify_local.sh frontend # frontend only
#
# To fix what it reports:  bash scripts/bootstrap_claude_cloud.sh
# For environment state:   bash scripts/project_doctor.sh
#
# Never prints secret VALUES.
set -uo pipefail
cd "$(dirname "$0")/.."

SCOPE="${1:-all}"
FAILED=0
declare -a RESULTS

head_() { printf '\n\033[1m%s\033[0m\n' "$*"; }
pass()  { printf '  \033[32mPASS\033[0m  %s\n' "$1"; RESULTS+=("PASS  $1"); }
fail()  { printf '  \033[31mFAIL\033[0m  %s\n' "$1"; RESULTS+=("FAIL  $1"); FAILED=1; }
skip()  { printf '  \033[33mSKIP\033[0m  %s\n' "$1"; RESULTS+=("SKIP  $1"); }

# Run a command quietly; print its tail only when it fails, so a green run
# stays readable and a red one tells you why without a re-run.
#
# `dir` runs it elsewhere WITHOUT a subshell. An earlier draft wrapped the
# frontend checks in `( cd frontend && ... )`, which meant `fail` appended to a
# copy of RESULTS that died with the subshell: a failing frontend printed FAIL
# and the script still exited 0. A verification script that cannot fail is
# worse than no verification script.
run() {
  local label="$1"; shift
  local dir="."
  if [ "$1" = "--in" ]; then dir="$2"; shift 2; fi
  local out rc
  out=$(cd "$dir" && "$@" 2>&1); rc=$?
  if [ $rc -eq 0 ]; then
    pass "$label"
  else
    fail "$label"
    printf '\033[2m%s\033[0m\n' "$(echo "$out" | tail -15 | sed 's/^/        /')"
  fi
}

# Real local services, if they are up. Exported rather than assumed: without
# these the durability tests fall back to their own default, and the point of
# this script is to run them for real.
if pg_isready -q 2>/dev/null; then
  export DATABASE_URL="${DATABASE_URL:-postgresql://agent_os:agent_os_dev@127.0.0.1:5432/agent_os}"
fi
if redis-cli ping >/dev/null 2>&1; then
  export REDIS_URL="${REDIS_URL:-redis://127.0.0.1:6379/0}"
fi

if [ "$SCOPE" = "all" ] || [ "$SCOPE" = "backend" ]; then
  head_ "Backend"
  if ! command -v uv >/dev/null 2>&1; then
    fail "uv is not installed"
  else
    run "ruff" uv run ruff check .
    run "deployment config" uv run python scripts/validate_deploy_config.py

    if pg_isready -q 2>/dev/null; then
      run "migrations apply" uv run python scripts/migrate.py
      # Idempotency is a promise the deploy process depends on, so check it
      # rather than trusting it.
      if uv run python scripts/migrate.py 2>&1 | grep -q "already up to date"; then
        pass "migrations idempotent"
      else
        fail "migrations idempotent (second run was not a no-op)"
      fi
      pass "real PostgreSQL reachable"
    else
      skip "migrations (no PostgreSQL — durability tests will not run)"
    fi

    redis-cli ping >/dev/null 2>&1 && pass "real Redis reachable" || skip "Redis (queue stays in-memory)"

    run "pytest" uv run pytest tests/ -q
  fi
fi

if [ "$SCOPE" = "all" ] || [ "$SCOPE" = "frontend" ]; then
  head_ "Frontend"
  if [ ! -d frontend/node_modules ]; then
    fail "frontend dependencies missing (cd frontend && pnpm install --frozen-lockfile)"
  else
    run "typecheck" --in frontend pnpm typecheck
    run "lint"      --in frontend pnpm lint
    run "tests"     --in frontend pnpm test
    run "build"     --in frontend pnpm build
  fi
fi

head_ "Result"
if [ "$FAILED" -ne 0 ] || printf '%s\n' "${RESULTS[@]}" | grep -q '^FAIL'; then
  printf '  \033[31mFAILED\033[0m — fix the FAIL lines above.\n'
  printf '  \033[2mUI changes still need real screenshots; this script does not render.\033[0m\n'
  exit 1
fi
printf '  \033[32mAll checks passed.\033[0m\n'
printf '  \033[2mThis proves the code. UI changes still need real screenshots\n'
printf '  (pnpm dev, then pnpm screenshot) — see CLAUDE.md section 3.\033[0m\n'
