# Gate 20C Retrieval Runtime Operator Status Export Build Plan

## Gate

Gate 20C — Retrieval Runtime Operator Status Export

## Purpose

Gate 20C consumes the Gate 20B runtime health surface and renders an operator-readable status export.

The export gives operators a concise view of retrieval runtime state without changing retrieval behavior.

## Non-Goals

Gate 20C does not:

- enable semantic vector retrieval
- enable hybrid retrieval
- introduce a new retrieval adapter
- change ranking behavior
- change retrieval execution
- commit generated `kbs/` runtime reports

## Operator Status Contract

The healthy operator export must report:

```text
status=RETRIEVAL_RUNTIME_HEALTHY
live_adapter=bm25_authoritative
bm25_authoritative=true
semantic_retrieval_enabled=false
hybrid_merge_enabled=false
fail_closed=true
action_required=none
```

If semantic retrieval is enabled or runtime fail-closed posture is lost, the export must report:

```text
action_required=investigate_runtime_health
```

## Files Planned

```text
backend/app/scripts/retrieval_runtime_operator_status_export.py
backend/app/scripts/validate_retrieval_runtime_operator_status_export.py
backend/app/scripts/run_gate20c_retrieval_runtime_operator_status_export.py
docs/checkpoints/Gate 20C Retrieval Runtime Operator Status Export Build Plan.md
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate20c_retrieval_runtime_operator_status_export
```

## Expected Validation Output

```text
[gate20c:operator-status] OK
[gate20c:operator-status] healthy_status=exported
[gate20c:operator-status] semantic_enabled=action_required
[gate20c:operator-status] fail_open=action_required
[gate20c:operator-status] action_required=none
[gate20c:operator-status] semantic_retrieval_enabled=false
[gate20c] Pipeline complete
[gate20c] Retrieval runtime operator status export preserves BM25-authoritative fail-closed posture
```

## Completion Criteria

Gate 20C is complete when:

1. A healthy Gate 20B report exports operator status with no action required.
2. Semantic-enabled drift exports operator action required.
3. Fail-open drift exports operator action required.
4. Local validation passes.
5. PR diff contains only Gate 20C source and checkpoint files.
6. No generated `kbs/` artifacts are committed.

## Next Gate Candidate

Gate 20D — Retrieval Runtime Operator Status Integration or CLI Surface.
