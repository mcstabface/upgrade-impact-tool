# Gate 19A Hybrid Retrieval Design Contract Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Hybrid Retrieval Design Contract  
Status: Proposed  
Generated: 2026-05-14

## Purpose

Gate 19A defines the hybrid retrieval design contract after the fixture vector retrieval path is proven.

This gate is design-only. It does not enable hybrid retrieval, does not make vector retrieval authoritative, does not enable production semantic retrieval, does not enable implicit reranking, and does not call an LLM.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/hybrid_retrieval_design_contract.py` | Builds hybrid retrieval design contract |
| `backend/app/scripts/validate_hybrid_retrieval_design_contract.py` | Validates retrieval boundaries and disabled semantic/hybrid flags |
| `backend/app/scripts/run_gate19a_hybrid_retrieval_design_contract.py` | Gate runner |

## Output Artifact

Gate 19A writes locally:

```text
kbs/retrieval/kb_hybrid_retrieval_design_contract.v1.json
```

## Contract Boundaries

Gate 19A requires:

```text
bm25_authoritative=true
vector_retrieval_authoritative=false
vector_retrieval_fixture_only=true
hybrid_merge_enabled=false
production_semantic_retrieval_enabled=false
implicit_reranking_enabled=false
draft_generation_enabled=false
llm_call_allowed=false
```

## Retrieval Modes

Gate 19A permits only these named modes:

```text
bm25_authoritative
vector_fixture_diagnostic
```

## Required Future Gates

Gate 19A declares the future work required before hybrid retrieval can become active:

```text
Gate 19B — Hybrid Retrieval Fixture Merge Plan
Gate 19C — Hybrid Retrieval Score Normalization Design
Gate 19D — Hybrid Retrieval Citation Preservation Validator
Gate 19E — Production Semantic Retrieval Enablement Gate
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate19a_hybrid_retrieval_design_contract
```

Expected output:

```text
[gate19a:hybrid-design] OK
[gate19a:hybrid-design] bm25_authoritative=preserved
[gate19a:hybrid-design] vector_retrieval=fixture_only
[gate19a:hybrid-design] hybrid_merge_enabled=false
[gate19a:hybrid-design] production_semantic_retrieval_enabled=false
```

Recommended next gate: **Gate 19B — Hybrid Retrieval Fixture Merge Plan**.
