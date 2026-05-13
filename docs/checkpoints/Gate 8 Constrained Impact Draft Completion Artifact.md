# Gate 8 Constrained Impact Draft Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: Constrained Impact Draft Generation  
Status: Complete for current sample corpus  
Generated: 2026-05-13

## Purpose

This checkpoint captures the completed state of Gate 8 for the KB ingestion/customization phase.

Gate 8 answered this bounded question:

> Can the system generate a constrained, citation-bound draft from the enriched evidence context while preserving draft/not-reviewed status and evidence-gap caveats?

For the current sample corpus, the answer is yes.

Gate 8 is not freeform impact generation. It uses deterministic templates and emits a citation-bound draft that remains explicitly not reviewed and not final.

## Source Baseline

Gate 8 starts from Gate 7 impact context enrichment and draft skeleton.

Current Gate 7 baseline:

- enriched context schema is `kb_impact_context.v2`
- enriched context status is `ENRICHED_EVIDENCE_ONLY_NO_GENERATED_CLAIMS`
- skeleton schema is `kb_impact_draft_skeleton.v1`
- skeleton status is `STRUCTURE_ONLY_NO_GENERATED_CLAIMS`
- evidence items: 15
- evidence groups: 10
- image-bearing evidence items: 15
- high-severity evidence exceptions: 10
- skeleton sections: 8
- all generation policy flags remain false
- validator passes with `[gate7:validate] OK`

## Gate 8 Pipeline

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate8_kb_impact_draft
```

Dry run:

```bash
python -m app.scripts.run_gate8_kb_impact_draft --dry-run
```

The orchestrator runs these modules in order:

1. `app.scripts.assemble_kb_impact_context`
2. `app.scripts.enrich_kb_impact_context`
3. `app.scripts.build_kb_impact_draft_skeleton`
4. `app.scripts.validate_kb_impact_draft_skeleton`
5. `app.scripts.generate_kb_impact_draft`
6. `app.scripts.validate_kb_impact_draft`
7. `app.scripts.write_kb_impact_draft_summary`

## Generated Artifacts

| Artifact | Purpose |
|---|---|
| `kbs/impact_context/kb_impact_context.v2.enriched.json` | Enriched evidence context with PFDS flags and evidence exceptions |
| `kbs/impact_context/kb_impact_draft_skeleton.v1.json` | Structure-only draft skeleton |
| `kbs/impact_context/kb_impact_draft.v1.json` | Constrained citation-bound draft JSON |
| `kbs/manifests/kb_impact_draft_summary.md` | Reviewer-facing draft summary |

Generated impact-context JSON artifacts remain ignored by Git:

```text
kbs/impact_context/
```

The Markdown summary remains reviewable and may be committed intentionally.

## Latest Verified Pipeline Output

Local clean run completed successfully with:

```text
python -m app.scripts.run_gate8_kb_impact_draft
```

Validation:

```text
[gate7:validate] OK
[gate8:validate] OK
```

Summary counts:

- Artifact type: `kb_impact_draft`
- Schema version: `kb_impact_draft.v1`
- Draft status: `DRAFT_CITATION_BOUND_NOT_REVIEWED_NOT_FINAL`
- Draft sections: 8
- Draft claims: 15
- Evidence citation count: 45
- Unresolved gaps: 10
- Image-bearing cited evidence: 15

## Draft Artifact Contract

The draft uses:

```text
artifact_type = kb_impact_draft
schema_version = kb_impact_draft.v1
draft_status = DRAFT_CITATION_BOUND_NOT_REVIEWED_NOT_FINAL
```

Generation policy:

```text
llm_used = false
generator = deterministic_template_v1
external_claims_allowed = false
claims_require_evidence_ids = true
missing_evidence_can_create_impact_claims = false
image_bearing_evidence_requires_visual_review_caveat = true
draft_review_status = NOT_REVIEWED_NOT_FINAL
```

## Draft Sections

| Section | Status | Claims | Unresolved Gaps |
|---|---|---:|---:|
| Scope and Inputs | `DRAFT_CITATION_BOUND_NOT_REVIEWED` | 1 | 0 |
| Evidence Groups | `DRAFT_CITATION_BOUND_NOT_REVIEWED` | 10 | 0 |
| Impacted Product Area: Oracle Utilities Customer Care and Billing | `DRAFT_CITATION_BOUND_NOT_REVIEWED` | 1 | 0 |
| Impacted Product Area: Oracle Utilities Service and Measurement Data Foundation | `DRAFT_CITATION_BOUND_NOT_REVIEWED` | 1 | 0 |
| Assumptions | `EMPTY_REVIEWER_REQUIRED` | 0 | 0 |
| Unresolved Evidence Gaps | `DRAFT_GAP_INVENTORY_NOT_REVIEWED` | 1 | 10 |
| Reviewer Notes | `EMPTY_REVIEWER_REQUIRED` | 0 | 0 |
| Draft Status | `DRAFT_NOT_REVIEWED_NOT_FINAL` | 1 | 0 |

## Claim Types

Gate 8 currently emits these deterministic claim types:

| Claim Type | Purpose |
|---|---|
| `source_scope` | Inventories source evidence packet size and cites all evidence IDs |
| `evidence_group_inventory` | Inventories each KB/bug/product/category evidence group |
| `retrieved_evidence_product_area` | Describes retrieved evidence concentration by product/category and bug references |
| `missing_evidence_inventory` | Lists high-severity missing-PFDS evidence gaps for reviewer follow-up |
| `draft_status` | States draft/not-reviewed/not-final status |

These are inventory and draft-control claims, not final reviewed impact conclusions.

## Citation and Caveat Rules

Gate 8 validator enforces:

- evidence-backed claims must cite evidence IDs,
- evidence-backed claims must include inline `[evidence: ...]` markers,
- cited evidence IDs must exist in the enriched context,
- claims citing image-bearing evidence must include visual inspection/review caveats,
- missing evidence may be inventoried but cannot create standalone impact claims,
- high-severity missing-PFDS exceptions remain listed as unresolved gaps,
- draft status cannot be final, reviewed, or approved.

## Current Draft Coverage

Current cited evidence coverage:

- Evidence items cited: 15
- Evidence groups cited: 10
- Evidence citation references: 45
- Image-bearing cited evidence: 15

Current product coverage:

| Product | Evidence Items |
|---|---:|
| Oracle Utilities Customer Care and Billing | 5 |
| Oracle Utilities Service and Measurement Data Foundation | 10 |

Current product/category draft inventory:

| Product | Categories |
|---|---|
| Oracle Utilities Customer Care and Billing | Billing (2), Case Management (2), Conversion (1) |
| Oracle Utilities Service and Measurement Data Foundation | Usage (10) |

## Unresolved Evidence Gaps

Gate 8 preserves the 10 high-severity missing-PFDS evidence exceptions from Gate 7. They are listed for reviewer follow-up and are not used as standalone impact conclusions.

Current unresolved gap products/categories include:

- Oracle Utilities Customer Care and Billing / Notification Preferences
- Oracle Utilities Customer Care and Billing / Customer 360
- Oracle Utilities Customer to Meter / Market Transaction Messaging

## Important Fix During Gate 8

The first Gate 8 validation run correctly failed because the deterministic draft status text included a forbidden conclusive phrase. The generator was patched to avoid that phrase while preserving not-final/not-reviewed meaning.

A second review found the same phrase in the Markdown summary interpretation text. The summary writer was patched as well so reviewer-facing output and validator constraints use aligned language.

This was a useful failure: it proved the validator can catch conclusive wording before a draft is accepted.

## Key Code Added or Updated During Gate 8

| Script | Purpose |
|---|---|
| `backend/app/scripts/generate_kb_impact_draft.py` | Builds deterministic citation-bound draft JSON |
| `backend/app/scripts/validate_kb_impact_draft.py` | Validates draft policy, citations, caveats, gaps, and not-final status |
| `backend/app/scripts/write_kb_impact_draft_summary.py` | Writes reviewer-facing draft summary |
| `backend/app/scripts/run_gate8_kb_impact_draft.py` | Runs Gate 8 end-to-end |

## Validation Coverage

Gate 8 validator checks:

- draft artifact type,
- draft schema version,
- draft status,
- generation policy flags,
- evidence-backed claims have evidence IDs,
- inline evidence markers exist,
- cited evidence IDs resolve to enriched context evidence items,
- image-bearing evidence claims include visual review caveats,
- unresolved gaps match high-severity evidence exceptions,
- section status is not final/reviewed/approved,
- forbidden final/conclusive fragments are absent from claim text.

## What This Proves

Gate 8 proves that the project can now:

- generate a deterministic draft artifact from enriched evidence context,
- keep draft output citation-bound,
- preserve unresolved evidence gaps,
- preserve visual-review caveats for image-bearing PFDS evidence,
- label the draft as not reviewed and not final,
- validate draft claims before accepting output,
- produce a reviewer-facing Markdown summary.

## Known Limitations

Gate 8 remains conservative and deterministic.

Known limitations:

- It does not call an LLM.
- It does not interpret images.
- It does not resolve missing PFDS evidence.
- It does not produce final impact analysis.
- It does not support reviewer edit workflow yet.
- It does not expose the draft in a web UI yet.
- The draft is inventory-oriented, not narrative-rich.

These limitations are acceptable for Gate 8. They define the next gate.

## Recommended Next Gate

Recommended next gate:

**Gate 9 — Draft Review Workflow and UI Surface**

Gate 9 should expose the draft, cited evidence IDs, caveats, and unresolved gaps in a reviewer-oriented workflow before any richer generation is introduced.

Proposed Gate 9 sequence:

1. Add draft review manifest:
   - draft artifact path,
   - review status,
   - reviewer fields,
   - accepted/rejected claim tracking,
   - unresolved gap acknowledgement tracking.
2. Add reviewer export/report:
   - draft sections,
   - evidence citations,
   - source lineage links/paths,
   - visual-review caveats,
   - unresolved gaps.
3. Add validation for review artifacts:
   - no claim can be marked accepted without evidence IDs,
   - image-bearing evidence requires visual-review acknowledgement,
   - unresolved gaps require reviewer acknowledgement before finalization.
4. Optionally expose the draft in the UI after the review artifact contract is stable.

Do not jump to richer generation before reviewer workflow exists.

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
- kbs/manifests/kb_impact_draft_summary.md
- backend/app/scripts/run_gate8_kb_impact_draft.py
- backend/app/scripts/generate_kb_impact_draft.py
- backend/app/scripts/validate_kb_impact_draft.py
- backend/app/scripts/write_kb_impact_draft_summary.py

Current Gate 8 status:
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

The Gate 8 pipeline runs successfully with:
python -m app.scripts.run_gate8_kb_impact_draft

Next recommended gate is Gate 9: Draft Review Workflow and UI Surface.

Please review the repo and produce the next concrete build plan and first patches for Gate 9.
Be specific, repo-grounded, and provide exact patch contents.
```

## Completion Status

Gate 8 is complete for the current source corpus.

The next work should begin from this checkpoint, not from memory.
