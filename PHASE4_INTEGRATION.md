# Phase 4 — Gemini Free-Tier Provider

Adds a real Gemini provider while retaining the mock provider for automated tests.

## Safe workflow

1. Extract this ZIP into the repository root.
2. Install/update dependencies:
   `pip install -e ".[dev]"`
3. Run `pytest`.
4. Do not add an API key to Git.
5. For a live smoke test, set environment variables only in the terminal.

## Live configuration

```bash
export AGENT_OS_LLM_PROVIDER=gemini
export GEMINI_API_KEY="YOUR_KEY"
export AGENT_OS_LLM_MODEL="gemini-3.1-flash-lite"
python scripts/gemini_smoke_test.py
```

The automated tests use mocks and do not consume Gemini quota.
