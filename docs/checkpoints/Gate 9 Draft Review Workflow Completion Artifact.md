# Gate 9 Draft Review Workflow Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: Draft Review Workflow and Reviewer Export  
Status: Complete for current sample corpus  
Generated: 2026-05-13

## Purpose

This checkpoint captures the completed state of Gate 9 for the KB ingestion/customization phase.

Gate 9 answered this bounded question:

> Can the constrained draft be turned into an explicit reviewer workflow with pending claim decisions, visual-review requirements, and unresolved-gap acknowledgements?

For the current sample corpus, the answer is yes.

Gate 9 does not finalize the draft, accept or reject claims automatically, call an LLM, add richer generation, or expose a web UI. It creates reviewer-operable artifacts before any UI surface or workflow automation.

## Source Baseline

Gate 9 starts from Gate 8 constrained citation-bound impact draft generation.

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

## Gate 9 Pipeline

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate9_kb_draft_review
```

Dry run:

```bash
python -m app.scripts.run_gate9_kb_draft_review --dry-run
```

The orchestrator runs these modules in order:

1. `app.scripts.run_gate8_kb_impact_draft`
2. `app.scripts.build_kb_draft_review_manifest`
3. `app.scripts.validate_kb_draft_review_manifest`
4. `app.scripts.write_kb_draft_review_export`

## Generated Artifacts

| Artifact | Purpose |
|---|---|
| `kbs/review/kb_draft_review_manifest.v1.json` | Machine-readable review workflow manifest |
| `kbs/manifests/kb_draft_review_export.md` | Reviewer-facing Markdown export |

Generated review JSON artifacts remain ignored by Git:

```text
kbs/review/
```

The Markdown export remains reviewable and may be committed intentionally.

## Latest Verified Pipeline Output

Local clean run completed successfully with:

```text
python -m app.scripts.run_gate9_kb_draft_review
```

Validation:

```text
[gate8:validate] OK
[gate9:validate] OK
```

Review export counts:

- Artifact type: `kb_draft_review_manifest`
- Schema version: `kb_draft_review_manifest.v1`
- Review status: `PENDING_REVIEW`
- Claim review tasks: 15
- Evidence review tasks: 13
- Visual review tasks: 13
- Unresolved gap tasks: 10
- Finalization allowed: `False`

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

## Claim Review Tasks

Each draft claim now has exactly one pending review task.

Initial task state:

```text
review_status = PENDING_REVIEW
reviewer_decision = UNSET
```

Task requirements are derived from the draft and enriched context:

- evidence-backed claims require evidence review,
- claims citing image-bearing evidence require visual review,
- gap/status claims without evidence citations do not require evidence or visual review.

Current task counts:

| Task Type | Count |
|---|---:|
| Claim review tasks | 15 |
| Evidence review tasks | 13 |
| Visual review tasks | 13 |
| Unresolved gap acknowledgement tasks | 10 |

## Claim Review Coverage

Gate 9 currently creates review tasks for these claim categories:

| Claim Type | Count | Review Requirement |
|---|---:|---|
| `source_scope` | 1 | Evidence + visual review |
| `evidence_group_inventory` | 10 | Evidence + visual review |
| `retrieved_evidence_product_area` | 2 | Evidence + visual review |
| `missing_evidence_inventory` | 1 | Gap acknowledgement / reviewer follow-up |
| `draft_status` | 1 | Reviewer awareness |

All evidence-backed review tasks start as `UNSET` and cannot be treated as accepted without explicit reviewer action.

## Unresolved Gap Acknowledgement Tasks

Each high-severity missing-PFDS exception from Gate 7/Gate 8 now has a pending acknowledgement task.

Initial gap task state:

```text
review_status = PENDING_ACKNOWLEDGEMENT
acknowledgement_status = UNSET
```

Current unresolved gap products/categories include:

- Oracle Utilities Customer Care and Billing / Notification Preferences
- Oracle Utilities Customer Care and Billing / Customer 360
- Oracle Utilities Customer to Meter / Market Transaction Messaging

## Reviewer Export

Reviewer-facing export:

```text
kbs/manifests/kb_draft_review_export.md
```

The export includes:

- review status and policy,
- claim review task table,
- evidence IDs and source lineage for each claim,
- visual review flags,
- claim text for review,
- reviewer decision placeholders,
- reviewer notes placeholders,
- unresolved gap acknowledgement task table,
- source draft/context paths.

## Key Code Added or Updated During Gate 9

| Script / Artifact | Purpose |
|---|---|
| `.gitignore` | Ignores generated `kbs/review/` artifacts |
| `backend/app/scripts/build_kb_draft_review_manifest.py` | Builds machine-readable pending review manifest |
| `backend/app/scripts/validate_kb_draft_review_manifest.py` | Validates review manifest invariants |
| `backend/app/scripts/write_kb_draft_review_export.py` | Writes reviewer-facing Markdown export |
| `backend/app/scripts/run_gate9_kb_draft_review.py` | Runs Gate 9 end-to-end |

## Validation Coverage

Gate 9 validator checks:

- review manifest artifact type,
- review manifest schema version,
- review status is pending,
- review policy flags,
- reviewer decision enum includes required values,
- every draft claim has a review task,
- no duplicate claim tasks,
- claim tasks reference known draft claim IDs,
- evidence IDs resolve to enriched context evidence items,
- evidence-backed tasks require evidence review,
- image-bearing evidence tasks require visual review,
- every unresolved gap has an acknowledgement task,
- gap tasks start unset,
- diagnostics match task counts.

## What This Proves

Gate 9 proves that the project can now:

- convert a citation-bound draft into explicit reviewer tasks,
- preserve evidence and visual-review obligations,
- expose unresolved evidence gaps as acknowledgement tasks,
- prevent finalization by policy,
- produce a reviewer-facing export without relying on UI state,
- keep review workflow state machine-readable.

## Known Limitations

Gate 9 remains artifact/workflow only.

Known limitations:

- It does not provide a web UI yet.
- It does not persist actual reviewer decisions beyond the generated manifest contract.
- It does not support claim acceptance/rejection update commands yet.
- It does not finalize drafts.
- It does not call an LLM.
- It does not add richer generated narrative.

These limitations are acceptable for Gate 9. They define the next gate.

## Recommended Next Gate

Recommended next gate:

**Gate 10 — Review UI Surface or Review Decision Update Commands**

There are two defensible next steps:

### Option A — Review Decision Update Commands

Add CLI tooling to update the review manifest safely before UI work:

1. `set_kb_review_claim_decision.py`
2. `set_kb_review_gap_acknowledgement.py`
3. validation that accepted evidence-backed claims still cite evidence,
4. validation that accepted image-bearing claims have visual acknowledgement,
5. validation that finalization remains blocked until all required tasks are complete.

### Option B — Review UI Surface

Expose the current review export/manifest in the UI:

1. list draft claims,
2. show evidence IDs and source lineage,
3. show visual-review flags,
4. show unresolved gaps,
5. defer mutation until the review update contract is stable.

Recommended order: **Option A before Option B**.

Do not build UI mutation before the review-decision artifact contract exists.

## Recommended Next Chat Starting Point

Use this prompt to continue in a new chat:

```text
We are continuing work on the Upgrade Impact Analysis Tool.

Gate 1 completed KB source extraction and PFDS evidence mapping.
Gate 2 completed KB PFDS source text extraction and deterministic chunking.
Gate 3 completed KB PFDS lexical retrieval index and query.
Gate 4 completed retrieval diagnostics and controls.
Gate 5 completed deterministic BM25 ranking and retrieval evaluation.
Gate 6 completed evidence-only impact context assembly.
Gate 7 completed impact context enrichment and draft skeleton.
Gate 8 completed constrained citation-bound impact draft generation.
Gate 9 completed draft review workflow and reviewer export.

Use this repo as source of truth:
mcstabface/upgrade-impact-tool

Start from these docs/artifacts:
- docs/checkpoints/Gate 1 KB Source Extraction Completion Artifact.md
- docs/checkpoints/Gate 2 KB Search Context Completion Artifact.md
- docs/checkpoints/Gate 3 KB PFDS Retrieval Completion Artifact.md
- docs/checkpoints/Gate 4 KB Retrieval Diagnostics Completion Artifact.md
- docs/checkpoints/Gate 5 BM25 Ranking Evaluation Completion Artifact.md
- docs/checkpoints/Gate 6 Impact Context Assembly Completion Artifact.md
- docs/checkpoints/Gate 7 Impact Context Enrichment Completion Artifact.md
- docs/checkpoints/Gate 8 Constrained Impact Draft Completion Artifact.md
- docs/checkpoints/Gate 9 Draft Review Workflow Completion Artifact.md
- kbs/manifests/kb_draft_review_export.md
- backend/app/scripts/run_gate9_kb_draft_review.py
- backend/app/scripts/build_kb_draft_review_manifest.py
- backend/app/scripts/validate_kb_draft_review_manifest.py
- backend/app/scripts/write_kb_draft_review_export.py

Current Gate 9 status:
- review manifest schema is `kb_draft_review_manifest.v1`
- review status is `PENDING_REVIEW`
- claim review tasks: 15
- evidence review tasks: 13
- visual review tasks: 13
- unresolved gap tasks: 10
- finalization allowed: false
- reviewer decisions default to `UNSET`
- validator passes with `[gate9:validate] OK`

The Gate 9 pipeline runs successfully with:
python -m app.scripts.run_gate9_kb_draft_review

Next recommended gate is Gate 10: Review Decision Update Commands, before UI mutation.

Please review the repo and produce the next concrete build plan and first patches for Gate 10.
Be specific, repo-grounded, and provide exact patch contents.
```

## Completion Status

Gate 9 is complete for the current source corpus.

The next work should begin from this checkpoint, not from memory.
