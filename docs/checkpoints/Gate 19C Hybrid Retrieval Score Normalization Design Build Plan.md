# Gate 19C Hybrid Retrieval Score Normalization Design Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Hybrid Retrieval Score Normalization Design  
Status: Proposed  
Generated: 2026-05-14

## Purpose

Gate 19C defines score normalization formulas for future hybrid retrieval.

This gate is design-only. It does not normalize live scores, does not write normalized scores, does not emit merged retrieval results, does not enable hybrid retrieval, does not enable production semantic retrieval, and does not enable reranking.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/hybrid_retrieval_score_normalization_design.py` | Builds design-only score normalization contract |
| `backend/app/scripts/validate_hybrid_retrieval_score_normalization_design.py` | Validates formulas remain specified but disabled |
| `backend/app/scripts/run_gate19c_hybrid_retrieval_score_normalization_design.py` | Gate runner |

## Input Plan

Gate 19C consumes or bootstraps locally:

```text
kbs/retrieval/kb_hybrid_retrieval_fixture_merge_plan.v1.json
```

Generated runtime artifacts are not committed to `main`.

## Output Artifact

Gate 19C writes locally:

```text
kbs/retrieval/kb_hybrid_retrieval_score_normalization_design.v1.json
```

## Design Formulas

Gate 19C specifies but does not execute:

```text
bm25_min_max_normalization
vector_cosine_shift_scale
weighted_hybrid_score
```

## Required Boundaries

Gate 19C requires:

```text
score_normalization_enabled=false
normalization_design_only=true
hybrid_merge_enabled=false
reranking_enabled=false
production_semantic_retrieval_enabled=false
bm25_authoritative=true
vector_retrieval_authoritative=false
normalized_scores_written=false
merged_results_written=false
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate19c_hybrid_retrieval_score_normalization_design
```

Expected output:

```text
[gate19c:score-design] OK
[gate19c:score-design] formulas=specified_not_enabled
[gate19c:score-design] normalized_scores_written=false
[gate19c:score-design] hybrid_merge_enabled=false
[gate19c:score-design] merged_results_written=false
```

Recommended next gate: **Gate 19D — Hybrid Retrieval Citation Preservation Validator**.
