# Phase 3 Integration

Phase 3 adds a provider-agnostic LLM execution layer, controlled parallel specialist execution,
verification, and retry while preserving the existing Phase 2 architecture.

## Install
```bash
unzip -o agent-os-phase3.zip
pip install -e ".[dev]"
pytest
```

## Environment
Copy `.env.example` to `.env` and add a provider key when you are ready to use a live LLM.

The default provider is `mock`, so the test suite does not require a paid API key.
