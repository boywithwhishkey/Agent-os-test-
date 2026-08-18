# Phase 5 — Autonomous LLM Orchestration

Phase 5 moves Agent OS from caller-supplied specialist tasks to LLM-generated task decomposition.

Flow:

`User objective -> LLM planner -> dynamic specialist jobs -> controlled parallel execution -> verifier -> final synthesizer`

## Test

```bash
pytest
```

## Mock-safe automated test

The test suite uses a deterministic provider, so it does not consume Gemini quota.

## Real Gemini run

```bash
export AGENT_OS_LLM_PROVIDER=gemini
export GEMINI_API_KEY='YOUR_KEY'
uvicorn app.main:app --reload
```

Then POST `/api/v1/autonomous/run`:

```json
{
  "objective": "Design a production-ready REST API for a task manager",
  "context": "Python, FastAPI, PostgreSQL"
}
```

The endpoint returns the generated plan, specialist results, verification feedback, and final synthesized answer.
