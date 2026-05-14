# Gate 18H Redaction Finding Triage Allowlist Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Redaction Finding Triage and Allowlist Design  
Status: Proposed  
Generated: 2026-05-13

## Purpose

Gate 18H triages Gate 18F redaction findings and defines a design-only allowlist policy.

This gate does not apply the allowlist, does not submit embedding requests, does not call an embedding model, and does not create vector files.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/redaction_finding_triage_allowlist.py` | Builds redaction triage report and design-only allowlist policy |
| `backend/app/scripts/validate_redaction_finding_triage_allowlist.py` | Validates classifier, policy, triage counts, and no vectors |
| `backend/app/scripts/run_gate18h_redaction_finding_triage_allowlist.py` | Gate runner |

## Source Artifacts

Gate 18H requires:

```text
kbs/retrieval/kb_embedding_full_text_requests.v1.jsonl
kbs/retrieval/kb_embedding_full_text_payload_report.v1.json
```

Gate 18H writes locally:

```text
kbs/retrieval/kb_embedding_redaction_triage_report.v1.json
```

Gate 18H must not write:

```text
kbs/retrieval/kb_embedding_batch_responses.v1.jsonl
kbs/retrieval/kb_vectors.v1.jsonl
kbs/retrieval/kb_vector_index.v1.json
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate18h_redaction_finding_triage_allowlist
```

Expected output:

```text
[gate18h:triage] OK
[gate18h:triage] classifier=valid
[gate18h:triage] allowlist_policy=design_only
[gate18h:triage] findings=triaged
[gate18h:triage] embedding_submission=forbidden
[gate18h:triage] vectors=not_created
```

Recommended next gate: **Gate 18I — Apply Reviewed Numeric Identifier Allowlist to Dry-Run Only**.
