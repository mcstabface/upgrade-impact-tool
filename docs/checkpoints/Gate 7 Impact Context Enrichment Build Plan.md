# Gate 7 Impact Context Enrichment Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Impact Context Enrichment and Draft Skeleton  
Status: Initial enrichment/skeleton slice  
Generated: 2026-05-12

## Starting Point

Gate 1 completed KB source extraction and PFDS evidence mapping.

Gate 2 completed matched PFDS source text extraction and deterministic chunking.

Gate 3 completed deterministic lexical retrieval over PFDS chunks.

Gate 4 completed retrieval diagnostics and controls.

Gate 5 completed deterministic BM25 ranking and retrieval evaluation.

Gate 6 completed evidence-only impact context assembly.

Current Gate 6 baseline:

- evidence-only impact context assembly works
- impact context has 15 evidence items
- impact context has 10 evidence groups
- 10 unique bug / patch numbers
- 10 unique child PDFs
- 0 warnings
- generation policy says LLM used = false
- generation policy says impact claims generated = false
- generation policy says summaries generated = false
- validator passes with `[gate6:validate] OK`

## Gate 7 Objective

Gate 7 answers this bounded question:

> Can the evidence packet be enriched with source-risk context and organized into a controlled draft skeleton without generating impact conclusions?

Gate 7 still does not generate upgrade impact analysis.

It adds:

- Gate 1 evidence exception context,
- Gate 2 PFDS text/image/highlight flags,
- a structure-only draft skeleton with evidence IDs and unresolved gaps.

## First Implementation Slice

Added scripts:

| Script | Purpose |
|---|---|
| `backend/app/scripts/enrich_kb_impact_context.py` | Reads Gate 6 impact context, Gate 2 search-context manifest, and Gate 1 exception summary; writes enriched impact context v2. |
| `backend/app/scripts/build_kb_impact_draft_skeleton.py` | Builds a structure-only draft skeleton from enriched context. |
| `backend/app/scripts/validate_kb_impact_draft_skeleton.py` | Validates enriched context and draft skeleton no-claims invariants. |
| `backend/app/scripts/write_kb_impact_draft_skeleton_summary.py` | Writes reviewer-facing Gate 7 summary. |
| `backend/app/scripts/run_gate7_kb_impact_skeleton.py` | Runs Gate 7 end-to-end. |

## Generated Outputs

| Artifact | Purpose |
|---|---|
| `kbs/impact_context/kb_impact_context.v2.enriched.json` | Enriched evidence-only impact context with PFDS flags and exception context. |
| `kbs/impact_context/kb_impact_draft_skeleton.v1.json` | Structure-only draft skeleton with sections and evidence IDs. |
| `kbs/manifests/kb_impact_draft_skeleton_summary.md` | Reviewer-facing Gate 7 summary. |

Generated impact-context JSON artifacts remain ignored by Git unless intentionally added.

## Run Commands

From backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate7_kb_impact_skeleton
```

Dry run:

```bash
python -m app.scripts.run_gate7_kb_impact_skeleton --dry-run
```

## Enriched Context Contract

The enriched context uses:

```text
artifact_type = kb_impact_context
schema_version = kb_impact_context.v2
assembly_status = ENRICHED_EVIDENCE_ONLY_NO_GENERATED_CLAIMS
```

Generation policy remains inherited from Gate 6:

```text
llm_used = false
impact_claims_generated = false
summaries_generated = false
```

Each evidence item gains:

```text
pdf_context_flags.status
pdf_context_flags.artifact_path
pdf_context_flags.has_images
pdf_context_flags.image_count
pdf_context_flags.has_highlight_annotations
pdf_context_flags.highlight_annotation_count
pdf_context_flags.text_extraction_status
pdf_context_flags.page_count
pdf_context_flags.char_count
```

The context also gains:

```text
evidence_exception_context.status_counts
evidence_exception_context.severity_counts
evidence_exception_context.high_severity_exceptions
```

## Draft Skeleton Contract

The draft skeleton uses:

```text
artifact_type = kb_impact_draft_skeleton
schema_version = kb_impact_draft_skeleton.v1
skeleton_status = STRUCTURE_ONLY_NO_GENERATED_CLAIMS
```

Generation policy:

```text
llm_used = false
impact_claims_generated = false
narrative_generated = false
```

Required sections:

- Scope and Inputs
- Evidence Groups
- Impacted Product Area sections
- Assumptions
- Unresolved Evidence Gaps
- Reviewer Notes
- No Generated Conclusion Status

The skeleton may include evidence IDs and explicit unresolved gap references. It must not include narrative impact conclusions.

## Acceptance Criteria

Gate 7 initial slice is complete when:

1. `python -m app.scripts.run_gate7_kb_impact_skeleton` completes successfully.
2. `kbs/impact_context/kb_impact_context.v2.enriched.json` exists locally.
3. `kbs/impact_context/kb_impact_draft_skeleton.v1.json` exists locally.
4. `kbs/manifests/kb_impact_draft_skeleton_summary.md` exists.
5. Validator passes with `[gate7:validate] OK`.
6. Every evidence item has PDF context flags.
7. Evidence exception context includes high-severity exceptions.
8. Skeleton has required sections.
9. Skeleton generation policy has all generated-claim flags false.
10. No generated impact conclusions are present.

## Non-Goals

Gate 7 does not:

- generate upgrade impact analysis,
- call an LLM,
- summarize evidence as impact,
- infer business conclusions,
- alter retrieval rankings,
- expose a web UI.

## Next Build Steps

### Step 1 — Run Gate 7 locally

```bash
python -m app.scripts.run_gate7_kb_impact_skeleton
```

Review:

```text
kbs/manifests/kb_impact_draft_skeleton_summary.md
```

### Step 2 — Add Gate 7 completion artifact

After a clean run, add:

```text
docs/checkpoints/Gate 7 Impact Context Enrichment Completion Artifact.md
```

### Step 3 — Next gate selection

Recommended next gate after Gate 7 completion:

**Gate 8 — Constrained Impact Draft Generation**

Gate 8 should generate draft language only inside controlled sections, require evidence IDs for every claim, preserve unresolved gaps, and explicitly label draft status.

## Notes

Gate 7 is the last non-generative staging gate before constrained draft generation. It should make missing evidence and visual/PDF risk visible before any text is generated.
