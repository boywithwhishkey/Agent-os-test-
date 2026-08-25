# THYNACT / Agent OS Project Instructions

## Source of truth
GitHub is the permanent source of truth.
Cloud Shell or any remote machine is only a disposable working environment.

## Repository workflow
- Always inspect existing code before editing.
- Preserve working functionality.
- Never expose secrets or API keys in frontend code or committed files.
- Keep secrets in environment variables or provider secret stores.
- Run relevant tests/checks before committing.
- Prefer small, reversible changes.
- Do not delete production resources unless explicitly requested.
- After meaningful verified changes:
  1. git status
  2. git diff
  3. run tests/checks
  4. commit with a clear message
  5. push to origin/main only when the change is verified

## Architecture
- Frontend: Cloudflare Pages
- Frontend domain: app.thynact.com
- Backend: Render
- Backend API domain: api.thynact.com
- Backend framework: FastAPI
- Repository contains frontend, backend, infrastructure, migrations, scripts and tests.
- Frontend must call protected backend operations through a secure server-side proxy/function where required.
- Never place AGENT_OS_API_KEY or provider secrets in browser-delivered HTML/JS.

## Development environment
Expected tools:
- Git
- GitHub CLI
- Python 3
- Node.js
- npm
- Wrangler
- Claude Code

## Project goal
Build THYNACT as a production-grade autonomous agent orchestration platform with reliable execution, verification, maintainable infrastructure and a polished responsive frontend.

## Safety
Never print, commit, log, or expose:
- API keys
- authentication tokens
- passwords
- private keys
- OAuth codes

Before destructive infrastructure changes, clearly identify impact first.
