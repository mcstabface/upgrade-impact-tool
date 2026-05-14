# Gate 18I Numeric Identifier Allowlist Dry Run Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Apply Reviewed Numeric Identifier Allowlist to Dry-Run Only  
Status: Proposed  
Generated: 2026-05-14

## Purpose

Gate 18I applies the Gate 18H numeric identifier allowlist candidates to dry-run reporting only.

This gate does not submit embedding requests, does not call an embedding model, does not create response JSONL, and does not create vector files.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/apply_numeric_allowlist_dry_run.py` | Applies numeric identifier allowlist candidates to dry-run reporting only |
| `backend/app/scripts/validate_numeric_allowlist_dry_run.py` | Validates count math, blocking status, and no vectors |
| `backend/app/scripts/run_gate18i_numeric_allowlist_dry_run.py` | Gate runner |

## Source Artifact

Gate 18I requires:

```text
kbs/retrieval/kb_embedding_redaction_triage_report.v1.json
```

Gate 18I writes locally:

```text
kbs/retrieval/kb_embedding_numeric_allowlist_dry_run_report.v1.json
```

Gate 18I must not write:

```text
kbs/retrieval/kb_embedding_batch_responses.v1.jsonl
kbs/retrieval/kb_vectors.v1.jsonl
kbs/retrieval/kb_vector_index.v1.json
```

## Current Expected Behavior

Based on Gate 18H:

```text
source_findings=42
allowlisted_findings=36
unresolved_findings=6
effective_blocking_findings=6
real_submission_allowed=false
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate18i_numeric_allowlist_dry_run
```

Expected output:

```text
[gate18i:allowlist] OK
[gate18i:allowlist] allowlist=applied_to_dry_run
[gate18i:allowlist] unresolved_findings=remain_blocking
[gate18i:allowlist] real_submission_allowed=false
[gate18i:allowlist] vectors=not_created
```

Recommended next gate: **Gate 18J — Unresolved Redaction Finding Review Export**.
