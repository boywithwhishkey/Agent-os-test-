# Phase 12 — Semantic Memory + pgvector

Features:
- provider-neutral embedding layer
- deterministic local embedding provider
- vector persistence
- pgvector cosine search
- HNSW index
- hybrid semantic + lexical ranking
- context compression

Apply:
```bash
unzip -o agent-os-phase12.zip
python scripts/apply_phase12.py
pytest
```

Expected: 49 passed.

Then:
```bash
python scripts/migrate_phase12.py
```
