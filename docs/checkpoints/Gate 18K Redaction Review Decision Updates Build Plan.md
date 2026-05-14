# Gate 18K Redaction Review Decision Updates Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Redaction Review Decision Update Commands  
Status: Proposed  
Generated: 2026-05-14

## Purpose

Gate 18K adds commands to update unresolved redaction review decisions.

This gate does not submit embedding requests, does not call an embedding model, does not create response JSONL, and does not create vector files.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/update_redaction_review_decisions.py` | Updates unresolved redaction review decisions in the review export JSON |
| `backend/app/scripts/validate_redaction_review_decision_updates.py` | Validates decision constraints and no vectors |
| `backend/app/scripts/run_gate18k_redaction_review_decision_updates.py` | Gate runner |

## Source Artifact

Gate 18K requires:

```text
kbs/retrieval/kb_embedding_unresolved_redaction_review.v1.json
```

## Supported Decisions

```text
PENDING
ALLOW_TECHNICAL_IDENTIFIER
MASK_BEFORE_EMBEDDING
BLOCK_EMBEDDING
```

Terminal decisions require reviewer notes.

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate18k_redaction_review_decision_updates
```

Expected output:

```text
[gate18k:review-update] OK
[gate18k:review-update] terminal_decisions=require_notes
[gate18k:review-update] unresolved_items=preserved
[gate18k:review-update] embedding_submission=forbidden
[gate18k:review-update] vectors=not_created
```

## Manual Update Command Shape

```bash
python -m app.scripts.update_redaction_review_decisions \
  --review-id redaction-review-0001 \
  --decision ALLOW_TECHNICAL_IDENTIFIER \
  --notes "Reviewed as a technical identifier." \
  --reviewer "reviewer-id"
```

Recommended next gate: **Gate 18L — Redaction Review Decision Summary Dry Run**.
