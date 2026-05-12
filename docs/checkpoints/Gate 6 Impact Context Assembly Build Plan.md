# Gate 6 Impact Context Assembly Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Impact Context Assembly  
Status: Initial evidence-only context assembly slice  
Generated: 2026-05-12

## Starting Point

Gate 1 completed KB source extraction and PFDS evidence mapping.

Gate 2 completed matched PFDS source text extraction and deterministic chunking.

Gate 3 completed deterministic lexical retrieval over PFDS chunks.

Gate 4 completed retrieval diagnostics and controls.

Gate 5 completed deterministic BM25 ranking and retrieval evaluation.

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

## Gate 6 Objective

Gate 6 answers this bounded question:

> Can the system assemble a structured evidence packet from validated retrieval results without generating impact claims?

This gate intentionally does not generate upgrade impact analysis.

It assembles retrieval evidence, lineage, scores, text, and grouping metadata into a reviewable impact-context artifact that later gates can use as input for constrained draft generation.

## First Implementation Slice

Added scripts:

| Script | Purpose |
|---|---|
| `backend/app/scripts/assemble_kb_impact_context.py` | Reads Gate 5 evaluation results, fetches full chunk rows from the SQLite index, and assembles an evidence-only impact-context artifact. |
| `backend/app/scripts/validate_kb_impact_context.py` | Validates evidence lineage and enforces no generated claims / no LLM use policy. |
| `backend/app/scripts/write_kb_impact_context_summary.py` | Produces a reviewer-facing Markdown summary of the evidence packet. |
| `backend/app/scripts/run_gate6_kb_impact_context.py` | Runs Gate 6 assembly, validation, and summary generation end-to-end. |

Updated:

| File | Purpose |
|---|---|
| `.gitignore` | Ignores generated `kbs/impact_context/` artifacts. |

## Generated Outputs

| Artifact | Purpose |
|---|---|
| `kbs/impact_context/kb_impact_context.v1.json` | Evidence-only impact-context artifact with selected chunks, full text, lineage, and evidence groups. |
| `kbs/manifests/kb_impact_context_summary.md` | Human-readable summary of the assembled evidence packet. |

Generated impact-context JSON is ignored by Git unless intentionally added.

## Run Commands

From backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate6_kb_impact_context
```

Dry run:

```bash
python -m app.scripts.run_gate6_kb_impact_context --dry-run
```

Direct assembly:

```bash
python -m app.scripts.assemble_kb_impact_context
```

Direct validation:

```bash
python -m app.scripts.validate_kb_impact_context
```

## Impact Context Artifact Contract

The artifact uses:

```text
artifact_type = kb_impact_context
schema_version = kb_impact_context.v1
assembly_status = EVIDENCE_ONLY_NO_GENERATED_CLAIMS
```

The generation policy must state:

```text
llm_used = false
impact_claims_generated = false
summaries_generated = false
```

This is the key invariant of Gate 6.

## Evidence Item Contract

Each evidence item preserves:

- evidence ID
- evaluation case ID
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

## Evidence Group Contract

Evidence groups are keyed by:

```text
{kb_document_id}::{bug_patch_number}::{product}::{category}
```

Each group includes:

- KB document ID
- bug / patch number
- product
- category
- evidence count
- max score
- child PDF paths
- evidence IDs

## Acceptance Criteria

Gate 6 initial slice is complete when:

1. `python -m app.scripts.run_gate6_kb_impact_context` completes successfully.
2. `kbs/impact_context/kb_impact_context.v1.json` exists locally.
3. `kbs/manifests/kb_impact_context_summary.md` exists.
4. Validator passes with `[gate6:validate] OK`.
5. Impact context `assembly_status` is `EVIDENCE_ONLY_NO_GENERATED_CLAIMS`.
6. Generation policy has all generated-claim flags set to false.
7. Evidence items are non-empty.
8. Evidence groups are non-empty.
9. Every evidence item has KB, bug/patch, product, category, child PDF, chunk ID, text hash, and text.
10. No impact conclusions are present.

## Non-Goals

Gate 6 does not:

- generate upgrade impact analysis,
- summarize evidence as impact,
- call an LLM,
- use embeddings,
- modify retrieval ranking,
- evaluate business relevance,
- expose a web UI.

## Next Build Steps

### Step 1 — Run Gate 6 locally

```bash
python -m app.scripts.run_gate6_kb_impact_context
```

Review:

```text
kbs/impact_context/kb_impact_context.v1.json
kbs/manifests/kb_impact_context_summary.md
```

### Step 2 — Add Gate 6 completion artifact

After a clean run, add:

```text
docs/checkpoints/Gate 6 Impact Context Assembly Completion Artifact.md
```

### Step 3 — Next gate selection

Recommended next gate after Gate 6 completion:

**Gate 7 — Constrained Impact Draft Skeleton**

Gate 7 should still avoid freeform analysis. It should produce a draft skeleton with explicit sections and citations to evidence IDs, while allowing empty/unknown sections where evidence is insufficient.

Do not jump straight to narrative generation.

## Notes

Gate 6 is the boundary between retrieval and downstream analysis. It turns validated retrieval outputs into a stable evidence packet. That packet is useful precisely because it is not yet an impact claim.
