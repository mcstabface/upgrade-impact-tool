# Gate 20A Retrieval Runtime Adapter Boundary Completion Artifact

## Gate

Gate 20A — Retrieval Runtime Adapter Boundary

## Status

Complete. Local validation passed.

## Purpose

Gate 20A establishes a fail-closed runtime adapter boundary for retrieval. The live retrieval path remains BM25-authoritative, and semantic or hybrid retrieval adapters are refused unless a future gate explicitly changes the boundary.

## Boundary Contract

The accepted runtime boundary is:

```text
live_adapter=bm25_authoritative
semantic_retrieval_enabled=false
hybrid_merge_enabled=false
bm25_authoritative=true
fail_closed=true
```

## Refused Adapter Classes

The boundary refuses:

- `semantic_vector`
- `hybrid_retrieval`
- unsupported adapter names
- invalid semantic enablement report paths

## Files Added

```text
backend/app/scripts/retrieval_runtime_adapter_boundary.py
backend/app/scripts/validate_retrieval_runtime_adapter_boundary.py
backend/app/scripts/run_gate20a_retrieval_runtime_adapter_boundary.py
docs/checkpoints/Gate 20A Retrieval Runtime Adapter Boundary Build Plan.md
```

## Validation Command

```bash
cd backend
python -m app.scripts.run_gate20a_retrieval_runtime_adapter_boundary
```

## Validation Output

```text
[gate20a:runtime-boundary] OK
[gate20a:runtime-boundary] default_adapter=bm25_authoritative
[gate20a:runtime-boundary] disabled_adapters=refused
[gate20a:runtime-boundary] unsupported_adapter=fail_closed
[gate20a:runtime-boundary] semantic_retrieval_enabled=false
[gate20a] Pipeline complete
[gate20a] Retrieval runtime boundary preserves BM25 authority and refuses semantic adapters
```

## Architectural Result

Gate 20A preserves the retrieval invariant that BM25 remains the authoritative runtime adapter. Semantic vector and hybrid retrieval paths cannot become active through runtime configuration drift or unsupported adapter names.

The boundary is explicit, locally validated, and fail-closed.

## Next Gate

Gate 20B — Retrieval Runtime Health Surface
