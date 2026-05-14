# Gate 19B Hybrid Retrieval Fixture Merge Plan Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Hybrid Retrieval Fixture Merge Plan  
Status: Proposed  
Generated: 2026-05-14

## Purpose

Gate 19B defines the fixture-only hybrid retrieval merge plan.

This gate does not emit merged retrieval results, does not enable hybrid retrieval, does not make vector retrieval authoritative, does not enable production semantic retrieval, and does not enable implicit reranking.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/hybrid_retrieval_fixture_merge_plan.py` | Builds fixture-only hybrid retrieval merge plan |
| `backend/app/scripts/validate_hybrid_retrieval_fixture_merge_plan.py` | Validates merge-plan boundaries and fail-closed design-contract checks |
| `backend/app/scripts/run_gate19b_hybrid_retrieval_fixture_merge_plan.py` | Gate runner |

## Input Contract

Gate 19B consumes or bootstraps locally:

```text
kbs/retrieval/kb_hybrid_retrieval_design_contract.v1.json
```

Generated runtime artifacts are not committed to `main`.

## Output Artifact

Gate 19B writes locally:

```text
kbs/retrieval/kb_hybrid_retrieval_fixture_merge_plan.v1.json
```

## Merge Plan Boundaries

Gate 19B requires:

```text
bm25_authoritative=true
vector_retrieval_authoritative=false
hybrid_merge_enabled=false
production_semantic_retrieval_enabled=false
score_normalization_enabled=false
reranking_enabled=false
citation_preservation_required=true
merge_output_mode=disabled_plan_only
```

## Merge Rules

Gate 19B defines but does not execute:

```text
collect_bm25_authoritative_candidates
collect_vector_fixture_candidates
preserve_citation_payloads
defer_score_normalization
disable_output_merge
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate19b_hybrid_retrieval_fixture_merge_plan
```

Expected output:

```text
[gate19b:merge-plan] OK
[gate19b:merge-plan] bm25_authoritative=preserved
[gate19b:merge-plan] vector_retrieval=diagnostic_only
[gate19b:merge-plan] hybrid_merge_enabled=false
[gate19b:merge-plan] citation_preservation=required
```

Recommended next gate: **Gate 19C — Hybrid Retrieval Score Normalization Design**.
