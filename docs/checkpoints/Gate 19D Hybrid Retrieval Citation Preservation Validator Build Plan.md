# Gate 19D Hybrid Retrieval Citation Preservation Validator Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Hybrid Retrieval Citation Preservation Validator  
Status: Proposed  
Generated: 2026-05-14

## Purpose

Gate 19D validates citation preservation requirements for future hybrid retrieval candidates.

This gate does not emit merged retrieval results, does not enable hybrid retrieval, does not enable production semantic retrieval, and does not enable score normalization or reranking.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/hybrid_retrieval_citation_preservation_validator.py` | Builds citation preservation report from fixture hybrid candidates |
| `backend/app/scripts/validate_hybrid_retrieval_citation_preservation.py` | Validates complete citations, missing-citation detection, missing-trace detection, and disabled merged output |
| `backend/app/scripts/run_gate19d_hybrid_retrieval_citation_preservation.py` | Gate runner |

## Input Design

Gate 19D consumes or bootstraps locally:

```text
kbs/retrieval/kb_hybrid_retrieval_score_normalization_design.v1.json
```

Generated runtime artifacts are not committed to `main`.

## Output Artifact

Gate 19D writes locally:

```text
kbs/retrieval/kb_hybrid_retrieval_citation_preservation.v1.json
```

## Required Citation Trace Fields

Every future hybrid retrieval candidate must preserve:

```text
source_artifact_path
kb_document_id
bug_patch_number
child_sha256
```

## Required Boundaries

Gate 19D requires:

```text
citation_preservation_required=true
hybrid_merge_enabled=false
merged_results_written=false
production_semantic_retrieval_enabled=false
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate19d_hybrid_retrieval_citation_preservation
```

Expected output:

```text
[gate19d:citation] OK
[gate19d:citation] citation_payloads=preserved
[gate19d:citation] trace_fields=complete
[gate19d:citation] missing_citation=detected
[gate19d:citation] merged_results_written=false
```

Recommended next gate: **Gate 19E — Production Semantic Retrieval Enablement Gate**.
