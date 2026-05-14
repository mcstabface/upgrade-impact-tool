# Gate 20F Retrieval Runtime Status Bundle Build Plan

## Gate

Gate 20F — Retrieval Runtime Status Bundle

## Purpose

Gate 20F creates an end-to-end retrieval runtime status bundle that aggregates the runtime boundary, runtime health surface, and operator status export into one deterministic status artifact.

The bundle gives operators and later integration hooks one stable place to inspect retrieval runtime posture.

## Non-Goals

Gate 20F does not:

- enable semantic vector retrieval
- enable hybrid retrieval
- introduce a new retrieval adapter
- change retrieval ranking
- change retrieval execution
- commit generated `kbs/` runtime reports

## Bundle Contract

The healthy bundle must report:

```text
status=RETRIEVAL_RUNTIME_STATUS_BUNDLE_READY
boundary_status=RETRIEVAL_RUNTIME_BOUNDARY_READY
health_status=RETRIEVAL_RUNTIME_HEALTHY
operator_action_required=none
live_adapter=bm25_authoritative
bm25_authoritative=true
semantic_retrieval_enabled=false
hybrid_merge_enabled=false
fail_closed=true
```

Semantic-enabled or fail-open drift must produce:

```text
status=RETRIEVAL_RUNTIME_STATUS_BUNDLE_UNHEALTHY
operator_action_required=investigate_runtime_health
```

## Files Planned

```text
backend/app/scripts/retrieval_runtime_status_bundle.py
backend/app/scripts/validate_retrieval_runtime_status_bundle.py
backend/app/scripts/run_gate20f_retrieval_runtime_status_bundle.py
docs/checkpoints/Gate 20F Retrieval Runtime Status Bundle Build Plan.md
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate20f_retrieval_runtime_status_bundle
```

## Expected Validation Output

```text
[gate20f:status-bundle] OK
[gate20f:status-bundle] healthy_bundle=ready
[gate20f:status-bundle] semantic_enabled=unhealthy
[gate20f:status-bundle] fail_open=unhealthy
[gate20f:status-bundle] live_adapter=bm25_authoritative
[gate20f:status-bundle] semantic_retrieval_enabled=false
[gate20f] Pipeline complete
[gate20f] Retrieval runtime status bundle preserves BM25-authoritative fail-closed posture
```

## Completion Criteria

Gate 20F is complete when:

1. A healthy status bundle is produced from healthy boundary/health/operator status.
2. Semantic-enabled drift produces an unhealthy bundle.
3. Fail-open drift produces an unhealthy bundle.
4. Local validation passes.
5. PR diff contains only Gate 20F source and checkpoint files.
6. No generated `kbs/` artifacts are committed.

## Next Gate Candidate

Gate 20G — Retrieval Runtime Status Bundle Documentation or Consumer Hook.
