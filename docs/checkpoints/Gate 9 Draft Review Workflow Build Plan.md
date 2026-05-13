# Gate 9 Draft Review Workflow Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Draft Review Workflow and Reviewer Export  
Status: Initial review-manifest slice  
Generated: 2026-05-13

## Starting Point

Gate 1 completed KB source extraction and PFDS evidence mapping.

Gate 2 completed matched PFDS source text extraction and deterministic chunking.

Gate 3 completed deterministic lexical retrieval over PFDS chunks.

Gate 4 completed retrieval diagnostics and controls.

Gate 5 completed deterministic BM25 ranking and retrieval evaluation.

Gate 6 completed evidence-only impact context assembly.

Gate 7 completed impact context enrichment and draft skeleton.

Gate 8 completed constrained citation-bound impact draft generation.

Current Gate 8 baseline:

- draft schema is `kb_impact_draft.v1`
- draft status is `DRAFT_CITATION_BOUND_NOT_REVIEWED_NOT_FINAL`
- generation policy says `llm_used = false`
- generation policy says `external_claims_allowed = false`
- generation policy says `claims_require_evidence_ids = true`
- generation policy says `missing_evidence_can_create_impact_claims = false`
- draft sections: 8
- draft claims: 15
- evidence citation count: 45
- unresolved gaps: 10
- image-bearing cited evidence: 15
- validator passes with `[gate8:validate] OK`

## Gate 9 Objective

Gate 9 answers this bounded question:

> Can the constrained draft be turned into an explicit reviewer workflow with pending claim decisions, visual-review requirements, and unresolved-gap acknowledgements?

Gate 9 does not finalize the draft and does not add richer generation.

It creates reviewer-operable artifacts before any UI surface or workflow automation.

## First Implementation Slice

Added scripts:

| Script | Purpose |
|---|---|
| `backend/app/scripts/build_kb_draft_review_manifest.py` | Builds a draft review manifest from the Gate 8 draft and enriched context. |
| `backend/app/scripts/validate_kb_draft_review_manifest.py` | Validates pending review tasks, evidence references, visual-review requirements, and gap acknowledgements. |
| `backend/app/scripts/write_kb_draft_review_export.py` | Writes reviewer-facing Markdown export for claims and unresolved gaps. |
| `backend/app/scripts/run_gate9_kb_draft_review.py` | Runs Gate 9 end-to-end, starting from Gate 8. |

Updated:

| File | Purpose |
|---|---|
| `.gitignore` | Ignores generated `kbs/review/` artifacts. |

## Generated Outputs

| Artifact | Purpose |
|---|---|
| `kbs/review/kb_draft_review_manifest.v1.json` | Machine-readable review workflow manifest. |
| `kbs/manifests/kb_draft_review_export.md` | Reviewer-facing Markdown export. |

Generated review JSON remains ignored by Git unless intentionally added.

## Run Commands

From backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate9_kb_draft_review
```

Dry run:

```bash
python -m app.scripts.run_gate9_kb_draft_review --dry-run
```

## Review Manifest Contract

The review manifest uses:

```text
artifact_type = kb_draft_review_manifest
schema_version = kb_draft_review_manifest.v1
review_status = PENDING_REVIEW
```

Review policy:

```text
claims_default_to_pending = true
accepted_claims_require_evidence_ids = true
image_bearing_claims_require_visual_acknowledgement = true
unresolved_gaps_require_acknowledgement = true
finalization_allowed = false
reviewer_decisions_allowed = UNSET, ACCEPT, REJECT, NEEDS_MORE_EVIDENCE
```

## Claim Review Task Contract

Each draft claim becomes a review task with:

- claim ID
- section ID
- claim type
- review status
- evidence IDs
- evidence-review requirement flag
- visual-review requirement flag
- reviewer decision
- reviewer notes

Initial reviewer decision is always:

```text
UNSET
```

Initial review status is always:

```text
PENDING_REVIEW
```

## Unresolved Gap Task Contract

Each unresolved evidence gap becomes an acknowledgement task with:

- gap ID
- review status
- gap text
- acknowledgement status
- reviewer notes

Initial acknowledgement status is always:

```text
UNSET
```

## Acceptance Criteria

Gate 9 initial slice is complete when:

1. `python -m app.scripts.run_gate9_kb_draft_review` completes successfully.
2. `kbs/review/kb_draft_review_manifest.v1.json` exists locally.
3. `kbs/manifests/kb_draft_review_export.md` exists.
4. Validator passes with `[gate9:validate] OK`.
5. Every draft claim has exactly one review task.
6. Evidence-backed claim tasks require evidence review.
7. Image-bearing evidence tasks require visual review.
8. Every unresolved gap has an acknowledgement task.
9. Review status remains pending.
10. Finalization remains disabled.

## Non-Goals

Gate 9 does not:

- accept or reject claims automatically,
- finalize impact drafts,
- call an LLM,
- add richer generation,
- expose a web UI yet.

## Next Build Steps

### Step 1 — Run Gate 9 locally

```bash
python -m app.scripts.run_gate9_kb_draft_review
```

Review:

```text
kbs/manifests/kb_draft_review_export.md
```

### Step 2 — Add Gate 9 completion artifact

After a clean run, add:

```text
docs/checkpoints/Gate 9 Draft Review Workflow Completion Artifact.md
```

### Step 3 — Next gate selection

Recommended next gate after Gate 9 completion:

**Gate 10 — Review UI Surface**

Gate 10 should expose the review export/manifest in the UI, but only after the artifact contract is stable.

## Notes

Gate 9 is the review-control boundary. It turns a citation-bound draft into a set of pending reviewer decisions. This must exist before any workflow is allowed to pretend it has been reviewed.
