# Gate 18T Fixture Vector Similarity Query Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Fixture Vector Similarity Query  
Status: Proposed  
Generated: 2026-05-14

## Purpose

Gate 18T adds fixture-only vector similarity query over certified vector artifacts.

This gate performs cosine similarity over the deterministic fixture vector set only. It does not enable production semantic retrieval and does not call an embedding model.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/fixture_vector_similarity_query.py` | Runs fixture-only cosine similarity query and writes query report |
| `backend/app/scripts/validate_fixture_vector_similarity_query.py` | Validates cosine behavior, deterministic top-k ordering, readiness guard, and fail-closed query IDs |
| `backend/app/scripts/run_gate18t_fixture_vector_similarity_query.py` | Gate runner |

## Source Artifacts

Gate 18T requires:

```text
kbs/retrieval/kb_vectors.v1.jsonl
kbs/retrieval/kb_vector_retrieval_readiness.v1.json
```

Gate 18T writes locally:

```text
kbs/retrieval/kb_fixture_vector_similarity_query.v1.json
```

## Query Behavior

Gate 18T validates:

```text
readiness report must be RETRIEVAL_READY
query vector defaults to first sorted vector_record_id
cosine self-similarity ranks first with score 1.0
results are sorted by descending score, then vector_record_id
unknown query vector IDs fail closed
production_retrieval_enabled=false
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate18t_fixture_vector_similarity_query
```

Expected output:

```text
[gate18t:similarity] OK
[gate18t:similarity] cosine=validated
[gate18t:similarity] fixture_query=deterministic
[gate18t:similarity] readiness_required=true
[gate18t:similarity] production_retrieval_enabled=false
```

Recommended next gate: **Gate 18U — Vector Query Result Citation Join**.
