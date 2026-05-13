# Gate 8 Constrained Impact Draft Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Constrained Impact Draft Generation  
Status: Initial citation-bound deterministic draft slice  
Generated: 2026-05-13

## Starting Point

Gate 1 completed KB source extraction and PFDS evidence mapping.

Gate 2 completed matched PFDS source text extraction and deterministic chunking.

Gate 3 completed deterministic lexical retrieval over PFDS chunks.

Gate 4 completed retrieval diagnostics and controls.

Gate 5 completed deterministic BM25 ranking and retrieval evaluation.

Gate 6 completed evidence-only impact context assembly.

Gate 7 completed impact context enrichment and draft skeleton.

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

## Gate 8 Objective

Gate 8 answers this bounded question:

> Can the system generate a constrained, citation-bound draft from the enriched evidence context while preserving draft/not-reviewed status and evidence-gap caveats?

Gate 8 is not freeform impact generation.

The first implementation slice uses deterministic templates, not an LLM.

## First Implementation Slice

Added scripts:

| Script | Purpose |
|---|---|
| `backend/app/scripts/generate_kb_impact_draft.py` | Generates a constrained citation-bound draft from enriched context and skeleton. |
| `backend/app/scripts/validate_kb_impact_draft.py` | Validates draft policy, evidence citations, image-bearing caveats, unresolved gaps, and not-final status. |
| `backend/app/scripts/write_kb_impact_draft_summary.py` | Writes reviewer-facing Gate 8 draft summary. |
| `backend/app/scripts/run_gate8_kb_impact_draft.py` | Runs Gate 8 end-to-end. |

## Generated Outputs

| Artifact | Purpose |
|---|---|
| `kbs/impact_context/kb_impact_draft.v1.json` | Constrained citation-bound draft artifact. |
| `kbs/manifests/kb_impact_draft_summary.md` | Reviewer-facing draft summary. |

Generated draft JSON remains ignored by Git unless intentionally added.

## Run Commands

From backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate8_kb_impact_draft
```

Dry run:

```bash
python -m app.scripts.run_gate8_kb_impact_draft --dry-run
```

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

## Citation Rules

Gate 8 validator enforces:

- evidence-backed claims must have evidence IDs,
- evidence-backed claims must contain an inline `[evidence: ...]` citation marker,
- cited evidence IDs must exist in the enriched context,
- claims citing image-bearing evidence must include visual inspection/review caveats,
- missing evidence may be inventoried but cannot become a standalone impact claim,
- draft cannot be final/reviewed/approved.

## Draft Sections

Generated sections:

- Scope and Inputs
- Evidence Groups
- Impacted Product Area sections
- Assumptions
- Unresolved Evidence Gaps
- Reviewer Notes
- Draft Status

The draft is intentionally conservative. It describes retrieved evidence inventory and category concentration. It does not claim business impact, root cause, severity, or final upgrade effect.

## Acceptance Criteria

Gate 8 initial slice is complete when:

1. `python -m app.scripts.run_gate8_kb_impact_draft` completes successfully.
2. `kbs/impact_context/kb_impact_draft.v1.json` exists locally.
3. `kbs/manifests/kb_impact_draft_summary.md` exists.
4. Validator passes with `[gate8:validate] OK`.
5. Every evidence-backed claim cites existing evidence IDs.
6. Every evidence-backed claim includes inline evidence markers.
7. Image-bearing evidence claims include visual-review caveats.
8. High-severity missing evidence remains listed as unresolved gaps.
9. Draft status remains not reviewed and not final.
10. No final impact conclusions are present.

## Non-Goals

Gate 8 does not:

- call an LLM,
- generate freeform impact analysis,
- claim business impact severity,
- resolve missing evidence,
- interpret images,
- expose a web UI.

## Next Build Steps

### Step 1 — Run Gate 8 locally

```bash
python -m app.scripts.run_gate8_kb_impact_draft
```

Review:

```text
kbs/manifests/kb_impact_draft_summary.md
```

### Step 2 — Add Gate 8 completion artifact

After a clean run, add:

```text
docs/checkpoints/Gate 8 Constrained Impact Draft Completion Artifact.md
```

### Step 3 — Next gate selection

Recommended next gate after Gate 8 completion:

**Gate 9 — Draft Review Workflow and UI Surface**

Gate 9 should expose the draft, evidence IDs, visual-review caveats, and unresolved gaps in a reviewer-oriented workflow before any broader automation.

## Notes

Gate 8 deliberately uses deterministic draft templates. This gives the project a safe draft artifact and validator before any future LLM-assisted drafting is introduced.
