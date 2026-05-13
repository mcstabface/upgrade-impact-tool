# Gate 18F Full Text Embedding Payload Redaction Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: Embedding Request Payload With Full Text and Redaction Check  
Status: Complete  
Generated: 2026-05-13

## Purpose

Gate 18F builds full-text embedding request payloads from the persisted embedding manifest and source chunk artifacts, then runs a conservative redaction scan.

This gate does not submit embedding requests, call an embedding model, or create vector files.

## Files Added

| File | Purpose |
|---|---|
| `backend/app/scripts/embedding_full_text_payload_plan.py` | Reconstructs full-text request payloads and writes payload report |
| `backend/app/scripts/validate_embedding_full_text_payload_plan.py` | Validates hashes, payload rows, redaction scan, and no vectors |
| `backend/app/scripts/run_gate18f_full_text_payload_redaction.py` | Gate runner |
| `docs/checkpoints/Gate 18F Full Text Embedding Payload Redaction Build Plan.md` | Build plan |

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

## Local Validation Result

```text
[gate18f:payload] Wrote full-text request JSONL: /home/stabby/Documents/upgrade-impact-tool/kbs/retrieval/kb_embedding_full_text_requests.v1.jsonl
[gate18f:payload] Wrote payload report: /home/stabby/Documents/upgrade-impact-tool/kbs/retrieval/kb_embedding_full_text_payload_report.v1.json
[gate18f:payload] requests=895
[gate18f:payload] redaction_findings=42
[gate18f:payload] embedding_submission=forbidden
[gate18f:payload] OK
[gate18f:payload] full_text=attached
[gate18f:payload] text_hashes=validated
[gate18f:payload] redaction_scan=enforced
[gate18f:payload] embedding_submission=forbidden
[gate18f:payload] vectors=not_created
[gate18f] Pipeline complete
[gate18f] Full-text embedding payloads are ready but not submitted
```

## Coverage

Gate 18F validates:

- full text is attached to request payload rows,
- chunk text hashes match the persisted embedding manifest,
- embedding input hashes match the persisted embedding manifest,
- citation payloads remain attached,
- conservative redaction patterns are detected,
- current corpus redaction findings are surfaced and block submission,
- embedding submission remains forbidden,
- no response JSONL is created,
- no vector JSONL is created,
- no vector index is created.

## Completion

Gate 18F is complete for the full-text payload and redaction enforcement slice.

Recommended next gate: **Gate 18G — Dry-Run Embedding Submission Contract**.
