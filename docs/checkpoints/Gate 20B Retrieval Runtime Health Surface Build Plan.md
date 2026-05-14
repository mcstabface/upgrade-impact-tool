# Gate 20B Retrieval Runtime Health Surface Build Plan

## Gate

Gate 20B — Retrieval Runtime Health Surface

## Purpose

Expose a deterministic retrieval runtime health surface that reports the active retrieval runtime posture without enabling semantic retrieval, hybrid merge, or vector authority.

Gate 20B builds on Gate 20A. Gate 20A owns the runtime adapter boundary. Gate 20B only reads that boundary and emits a health report.

## Non-Goals

Gate 20B does not:

- enable semantic vector retrieval
- enable hybrid retrieval
- introduce a new retrieval adapter
- change ranking or retrieval behavior
- write generated `kbs/` artifacts to the repository

## Health Contract

The healthy runtime posture is:

```text
live_adapter=bm25_authoritative
selected_adapter=bm25_authoritative
bm25_authoritative=true
semantic_retrieval_enabled=false
hybrid_merge_enabled=false
fail_closed=true
```

## Files Planned

```text
backend/app/scripts/retrieval_runtime_health_surface.py
backend/app/scripts/validate_retrieval_runtime_health_surface.py
backend/app/scripts/run_gate20b_retrieval_runtime_health_surface.py
docs/checkpoints/Gate 20B Retrieval Runtime Health Surface Build Plan.md
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate20b_retrieval_runtime_health_surface
```

## Expected Validation Output

```text
[gate20b:runtime-health] OK
[gate20b:runtime-health] healthy_boundary=pass
[gate20b:runtime-health] semantic_enabled=unhealthy
[gate20b:runtime-health] fail_open=unhealthy
[gate20b:runtime-health] bm25_authoritative=true
[gate20b:runtime-health] semantic_retrieval_enabled=false
[gate20b] Pipeline complete
[gate20b] Retrieval runtime health surface exposes BM25-authoritative fail-closed state
```

## Completion Criteria

Gate 20B is complete when:

1. The health report marks the Gate 20A boundary healthy only when BM25 is authoritative.
2. Semantic retrieval enabled state is reported unhealthy.
3. Fail-open state is reported unhealthy.
4. Local validation passes.
5. PR diff contains only Gate 20B source and checkpoint files.
6. No generated `kbs/` artifacts are committed.

## Next Gate Candidate

Gate 20C — Retrieval Runtime Health Surface Consumption or Operator Status Export.
