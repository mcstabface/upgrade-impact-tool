# Gate 18G Dry Run Embedding Submission Contract Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Dry-Run Embedding Submission Contract  
Status: Proposed  
Generated: 2026-05-13

## Purpose

Gate 18G defines and validates the dry-run embedding submission boundary.

This gate reads the Gate 18F full-text request payload and payload report, then writes a dry-run submission report. It does not submit embedding requests, call an embedding model, create response JSONL, or create vector files.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/embedding_dry_run_submission_contract.py` | Builds dry-run submission decision and report |
| `backend/app/scripts/validate_embedding_dry_run_submission_contract.py` | Validates refusal/ready decisions, schema, and no vectors |
| `backend/app/scripts/run_gate18g_dry_run_embedding_submission_contract.py` | Gate runner |

## Source Artifacts

Gate 18G requires:

```text
kbs/retrieval/kb_embedding_full_text_requests.v1.jsonl
kbs/retrieval/kb_embedding_full_text_payload_report.v1.json
```

Gate 18G writes locally:

```text
kbs/retrieval/kb_embedding_dry_run_submission_report.v1.json
```

Gate 18G must not write:

```text
kbs/retrieval/kb_embedding_batch_responses.v1.jsonl
kbs/retrieval/kb_vectors.v1.jsonl
kbs/retrieval/kb_vector_index.v1.json
```

## Current Expected Behavior

The current Gate 18F payload report contains redaction findings. Gate 18G should therefore produce:

```text
status=REFUSED
reason=REDACTION_FINDINGS_PRESENT
real_submission_allowed=false
vectors_created=false
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate18g_dry_run_embedding_submission_contract
```

Expected output:

```text
[gate18g:dry-run] OK
[gate18g:dry-run] contract=valid
[gate18g:dry-run] redaction_findings=refuse_submission
[gate18g:dry-run] real_submission_allowed=false
[gate18g:dry-run] simulated_response_schema=valid
[gate18g:dry-run] vectors=not_created
```

Recommended next gate: **Gate 18H — Redaction Finding Triage and Allowlist Design**.
