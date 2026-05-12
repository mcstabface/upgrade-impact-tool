# Gate 6 Impact Context Assembly Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: Impact Context Assembly  
Status: Complete for current sample corpus  
Generated: 2026-05-12

## Purpose

This checkpoint captures the completed state of Gate 6 for the KB ingestion/customization phase.

Gate 6 answered this bounded question:

> Can the system assemble a structured evidence packet from validated retrieval results without generating impact claims?

For the current sample corpus, the answer is yes.

Gate 6 is evidence assembly only. It does not generate upgrade impact analysis, infer business truth, call an LLM, use embeddings, or summarize retrieved evidence as impact.

## Source Baseline

Gate 6 starts from Gate 5 retrieval evaluation.

Current Gate 5 baseline:

- 179 indexed PFDS chunk collections
- 895 indexed PFDS chunks
- 79,073 posting rows
- 4,857 vocabulary terms
- TF-IDF and BM25 rankers are supported
- BM25 diagnostics include k1, b, average document length, and score contributions
- BM25 comparison summary is generated
- retrieval evaluation fixture has 3 cases
- evaluation passes with 3 passed / 0 failed
- validators pass with `[gate3:validate] OK`, `[gate4:validate] OK`, and `[gate5:validate] OK`

## Gate 6 Pipeline

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate6_kb_impact_context
```

Dry run:

```bash
python -m app.scripts.run_gate6_kb_impact_context --dry-run
```

The orchestrator runs these modules in order:

1. `app.scripts.assemble_kb_impact_context`
2. `app.scripts.validate_kb_impact_context`
3. `app.scripts.write_kb_impact_context_summary`

## Generated Artifacts

| Artifact | Purpose |
|---|---|
| `kbs/impact_context/kb_impact_context.v1.json` | Evidence-only impact-context artifact with selected chunks, full text, lineage, and evidence groups |
| `kbs/manifests/kb_impact_context_summary.md` | Human-readable summary of the assembled evidence packet |

Generated impact-context JSON is ignored by Git:

```text
kbs/impact_context/
```

The Markdown summary remains reviewable and may be committed intentionally.

## Latest Verified Pipeline Output

Local clean run completed successfully with:

```text
python -m app.scripts.run_gate6_kb_impact_context
```

Validation:

```text
[gate6:validate] OK
```

Summary counts:

- Evidence items: 15
- Evidence groups: 10
- Unique bug / patch numbers: 10
- Unique child PDFs: 10
- Warnings: 0

## Impact Context Contract

The artifact uses:

```text
artifact_type = kb_impact_context
schema_version = kb_impact_context.v1
assembly_status = EVIDENCE_ONLY_NO_GENERATED_CLAIMS
```

The generation policy is:

```text
llm_used = false
impact_claims_generated = false
summaries_generated = false
```

Allowed use:

```text
Evidence packet for reviewer inspection and later constrained impact-draft generation.
```

Prohibited use:

```text
Do not treat this artifact as an impact analysis or business conclusion.
```

## Source Inputs

Gate 6 consumes:

```text
kbs/manifests/kb_retrieval_eval_results.json
kbs/indexes/kb_chunk_lexical_index.sqlite
```

The current context includes the top 5 retrieval results per passing evaluation case.

## Evidence by Evaluation Case

| Case | Evidence Items |
|---|---:|
| `billing_usage_filtered_ccb_bm25` | 5 |
| `rates_filtered_smdf_usage_bm25` | 5 |
| `usage_rates_unfiltered_bm25` | 5 |

## Product Breakdown

| Product | Evidence Items |
|---|---:|
| Oracle Utilities Service and Measurement Data Foundation | 10 |
| Oracle Utilities Customer Care and Billing | 5 |

## Category Breakdown

| Category | Evidence Items |
|---|---:|
| Usage | 10 |
| Billing | 2 |
| Case Management | 2 |
| Conversion | 1 |

## Evidence Groups

Evidence groups are keyed by:

```text
{kb_document_id}::{bug_patch_number}::{product}::{category}
```

Current groups:

| KB | Bug / Patch | Product | Category | Evidence Count | Max Score |
|---|---|---|---|---:|---:|
| KB875759 | 39002995 | Oracle Utilities Service and Measurement Data Foundation | Usage | 2 | 8.97746 |
| KB881136 | 39007114 | Oracle Utilities Service and Measurement Data Foundation | Usage | 2 | 8.97746 |
| KB881135 | 39127058 | Oracle Utilities Service and Measurement Data Foundation | Usage | 2 | 8.016685 |
| KB875759 | 38794940 | Oracle Utilities Service and Measurement Data Foundation | Usage | 2 | 7.735204 |
| KB881136 | 38966530 | Oracle Utilities Service and Measurement Data Foundation | Usage | 2 | 6.779924 |
| KB869018 | 38848234 | Oracle Utilities Customer Care and Billing | Billing | 1 | 4.557985 |
| KB881135 | 39234264 | Oracle Utilities Customer Care and Billing | Billing | 1 | 4.498597 |
| KB881135 | 39064768 | Oracle Utilities Customer Care and Billing | Conversion | 1 | 4.477924 |
| KB881135 | 38959224 | Oracle Utilities Customer Care and Billing | Case Management | 1 | 4.324562 |
| KB881136 | 38959233 | Oracle Utilities Customer Care and Billing | Case Management | 1 | 4.324562 |

## Evidence Item Contract

Each evidence item preserves:

- evidence ID
- source evaluation case ID
- query
- ranker
- retrieval rank
- retrieval score
- chunk ID
- matched terms
- KB document ID
- maintenance pack
- bug / patch number
- product
- category
- portfolio file
- child PDF path
- child SHA-256
- collection path
- source artifact path
- chunk index/count
- character offsets
- text SHA-256
- full chunk text

## Validation Coverage

Gate 6 validator checks:

- artifact type is `kb_impact_context`,
- schema version is `kb_impact_context.v1`,
- assembly status is `EVIDENCE_ONLY_NO_GENERATED_CLAIMS`,
- `llm_used` is false,
- `impact_claims_generated` is false,
- `summaries_generated` is false,
- evidence items are non-empty,
- evidence groups are non-empty,
- every evidence item has required lineage fields,
- evidence IDs are unique,
- evidence item text is non-empty,
- evidence group IDs resolve to evidence items,
- diagnostics report positive evidence and group counts.

## What This Proves

Gate 6 proves that the project can now:

- consume passing retrieval evaluation results,
- fetch full evidence chunk rows from the SQLite index,
- assemble a structured evidence-only impact context,
- preserve retrieval rank, score, and matched terms,
- preserve full KB/PFDS source lineage,
- group evidence by KB, bug/patch, product, and category,
- validate that no generated claims are present,
- produce a reviewer-facing evidence packet summary.

## Known Limitations

Gate 6 remains evidence assembly only.

Known limitations:

- It only assembles evidence from the current retrieval evaluation fixture.
- It includes top 5 results per passing evaluation case by default.
- It does not yet merge Gate 1 missing-evidence warnings into the impact context.
- It does not include image-bearing PFDS flags yet.
- It does not expose impact context in the web UI yet.
- It does not generate impact analysis.
- It does not generate summaries.
- It does not call an LLM.

These limitations are acceptable for Gate 6. They define the next gate.

## Recommended Next Gate

Recommended next gate:

**Gate 7 — Impact Context Enrichment and Draft Skeleton**

Gate 7 should enrich the evidence packet before any narrative impact generation.

Proposed Gate 7 sequence:

1. Merge Gate 1 evidence exception warnings into impact context:
   - missing PFDS evidence rows,
   - KB-declared no-PFD rows,
   - non-joinable rows,
   - portfolio no-PFDS placeholders.
2. Merge Gate 2 PDF context flags into impact evidence items:
   - image-bearing artifact flag,
   - image count,
   - highlight annotation flag,
   - text extraction status.
3. Add draft skeleton artifact with empty controlled sections:
   - impacted product areas,
   - evidence groups,
   - assumptions,
   - unresolved evidence gaps,
   - reviewer notes,
   - no generated conclusion status.
4. Validate that the skeleton contains structure and citations only, not narrative conclusions.
5. Only after this is stable, allow constrained impact-draft generation.

Do not jump to freeform impact analysis yet. The next step is enriched evidence and a structured draft container.

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

Use this repo as source of truth:
mcstabface/upgrade-impact-tool

Start from these docs/artifacts:
- docs/checkpoints/Gate 1 KB Source Extraction Completion Artifact.md
- docs/checkpoints/Gate 2 KB Search Context Completion Artifact.md
- docs/checkpoints/Gate 3 KB PFDS Retrieval Completion Artifact.md
- docs/checkpoints/Gate 4 KB Retrieval Diagnostics Completion Artifact.md
- docs/checkpoints/Gate 5 BM25 Ranking Evaluation Completion Artifact.md
- docs/checkpoints/Gate 6 Impact Context Assembly Completion Artifact.md
- kbs/manifests/kb_impact_context_summary.md
- kbs/manifests/kb_retrieval_eval_results.json
- backend/app/scripts/run_gate6_kb_impact_context.py
- backend/app/scripts/assemble_kb_impact_context.py
- backend/app/scripts/validate_kb_impact_context.py

Current Gate 6 status:
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

The Gate 6 pipeline runs successfully with:
python -m app.scripts.run_gate6_kb_impact_context

Next recommended gate is Gate 7: Impact Context Enrichment and Draft Skeleton.

Please review the repo and produce the next concrete build plan and first patches for Gate 7.
Be specific, repo-grounded, and provide exact patch contents.
```

## Completion Status

Gate 6 is complete for the current source corpus.

The next work should begin from this checkpoint, not from memory.
