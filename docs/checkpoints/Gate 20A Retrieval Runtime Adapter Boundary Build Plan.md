# Gate 20A Retrieval Runtime Adapter Boundary Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Retrieval Runtime Adapter Boundary  
Status: Proposed  
Generated: 2026-05-14

## Purpose

Gate 20A defines the retrieval runtime adapter boundary after production semantic retrieval enablement remains disabled.

This gate keeps the live retrieval adapter on the BM25-authoritative path. Semantic vector and hybrid retrieval adapters remain disabled and fail closed.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/retrieval_runtime_adapter_boundary.py` | Builds retrieval runtime adapter boundary report and selection behavior |
| `backend/app/scripts/validate_retrieval_runtime_adapter_boundary.py` | Validates BM25 default selection, disabled adapter refusal, unsupported adapter refusal, and invalid enablement refusal |
| `backend/app/scripts/run_gate20a_retrieval_runtime_adapter_boundary.py` | Gate runner |

## Input Report

Gate 20A consumes or bootstraps locally:

```text
kbs/retrieval/kb_production_semantic_retrieval_enablement_gate.v1.json
```

Generated runtime artifacts are not committed to `main`.

## Output Artifact

Gate 20A writes locally:

```text
kbs/retrieval/kb_retrieval_runtime_adapter_boundary.v1.json
```

## Runtime Boundary

Supported live adapter:

```text
bm25_authoritative
```

Disabled adapters:

```text
semantic_vector
hybrid_retrieval
```

## Required Default State

Gate 20A requires:

```text
live_adapter=bm25_authoritative
semantic_retrieval_enabled=false
hybrid_merge_enabled=false
bm25_authoritative=true
fail_closed=true
```

## Blocking Cases

Gate 20A refuses:

```text
semantic_vector adapter request
hybrid_retrieval adapter request
unsupported adapter request
invalid production semantic retrieval enablement report
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate20a_retrieval_runtime_adapter_boundary
```

Expected output:

```text
[gate20a:runtime-boundary] OK
[gate20a:runtime-boundary] default_adapter=bm25_authoritative
[gate20a:runtime-boundary] disabled_adapters=refused
[gate20a:runtime-boundary] unsupported_adapter=fail_closed
[gate20a:runtime-boundary] semantic_retrieval_enabled=false
```

Recommended next gate: **Gate 20B — Retrieval Runtime Health Surface**.
