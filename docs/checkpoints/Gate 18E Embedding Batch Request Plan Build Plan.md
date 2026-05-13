# Gate 18E Embedding Batch Request Plan Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Embedding Batch Request Plan  
Status: Proposed  
Generated: 2026-05-13

## Purpose

Gate 18E builds a deterministic embedding batch request plan from the persisted Gate 18D embedding manifest skeleton.

This gate does not submit embedding requests, does not call an embedding model, and does not create vector files.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/embedding_batch_request_plan.py` | Builds request-plan JSON and request JSONL from the persisted manifest skeleton |
| `backend/app/scripts/validate_embedding_batch_request_plan.py` | Validates request-plan and request JSONL structure |
| `backend/app/scripts/run_gate18e_embedding_batch_request_plan.py` | Gate runner |

## Source Artifact

Gate 18E requires:

```text
kbs/retrieval/kb_embedding_manifest.v1.json
```

Gate 18E writes locally:

```text
kbs/retrieval/kb_embedding_batch_request_plan.v1.json
kbs/retrieval/kb_embedding_batch_requests.v1.jsonl
```

Gate 18E must not write:

```text
kbs/retrieval/kb_embedding_batch_responses.v1.jsonl
kbs/retrieval/kb_vectors.v1.jsonl
kbs/retrieval/kb_vector_index.v1.json
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate18e_embedding_batch_request_plan
```

Expected output:

```text
[gate18e:request-plan] OK
[gate18e:request-plan] request_plan=valid
[gate18e:request-plan] request_jsonl=valid
[gate18e:request-plan] idempotency=request_ids_cache_keys
[gate18e:request-plan] embedding_submission=forbidden
[gate18e:request-plan] vectors=not_created
```

Recommended next gate: **Gate 18F — Embedding Request Payload With Full Text and Redaction Check**.
