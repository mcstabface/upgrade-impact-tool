# Gate 18F Full Text Embedding Payload Redaction Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Embedding Request Payload With Full Text and Redaction Check  
Status: Proposed  
Generated: 2026-05-13

## Purpose

Gate 18F builds full-text embedding request payloads from the persisted embedding manifest and source chunk artifacts, then runs a conservative redaction scan.

This gate does not submit embedding requests, call an embedding model, or create vector files.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/embedding_full_text_payload_plan.py` | Reconstructs full-text request payloads and writes payload report |
| `backend/app/scripts/validate_embedding_full_text_payload_plan.py` | Validates hashes, payload rows, redaction scan, and no vectors |
| `backend/app/scripts/run_gate18f_full_text_payload_redaction.py` | Gate runner |

## Source Artifacts

Gate 18F requires:

```text
kbs/retrieval/kb_embedding_manifest.v1.json
kbs/manifests/kb_search_context_chunks_manifest.json
kbs/search_context_chunks/
```

Gate 18F writes locally:

```text
kbs/retrieval/kb_embedding_full_text_requests.v1.jsonl
kbs/retrieval/kb_embedding_full_text_payload_report.v1.json
```

Gate 18F must not write:

```text
kbs/retrieval/kb_embedding_batch_responses.v1.jsonl
kbs/retrieval/kb_vectors.v1.jsonl
kbs/retrieval/kb_vector_index.v1.json
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate18f_full_text_payload_redaction
```

Expected output:

```text
[gate18f:payload] OK
[gate18f:payload] full_text=attached
[gate18f:payload] text_hashes=validated
[gate18f:payload] redaction_scan=enforced
[gate18f:payload] embedding_submission=forbidden
[gate18f:payload] vectors=not_created
```

A conservative redaction finding does not fail this gate. It blocks submission and keeps `embedding_submission=forbidden`.

Recommended next gate: **Gate 18G — Dry-Run Embedding Submission Contract**.
