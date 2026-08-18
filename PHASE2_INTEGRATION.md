# Phase 2
Extract into the repository root.

Add to `app/main.py`:
```python
from app.api.orchestration import router as orchestration_router
app.include_router(orchestration_router)
```

Then run:
```bash
pip install pytest-asyncio
pytest
```

This checkpoint intentionally uses provider-independent mock execution. Real LLM calls, PostgreSQL, retries and n8n come after the orchestration contract passes.
