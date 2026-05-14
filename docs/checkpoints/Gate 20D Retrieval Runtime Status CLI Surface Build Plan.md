# Gate 20D Retrieval Runtime Status CLI Surface Build Plan

## Gate

Gate 20D — Retrieval Runtime Status CLI Surface

## Purpose

Gate 20D exposes the Gate 20C retrieval runtime operator status through a direct CLI status surface.

This gives operators a simple command to inspect runtime posture without changing retrieval behavior.

## Non-Goals

Gate 20D does not:

- enable semantic vector retrieval
- enable hybrid retrieval
- introduce a new retrieval adapter
- change retrieval ranking
- change retrieval execution
- commit generated `kbs/` runtime reports

## CLI Contract

The CLI supports:

```text
--format text
--format json
```

The healthy CLI status must report:

```text
status=RETRIEVAL_RUNTIME_HEALTHY
live_adapter=bm25_authoritative
bm25_authoritative=true
semantic_retrieval_enabled=false
hybrid_merge_enabled=false
fail_closed=true
action_required=none
```

Unsupported formats must fail closed.

## Files Planned

```text
backend/app/scripts/retrieval_runtime_status_cli.py
backend/app/scripts/validate_retrieval_runtime_status_cli.py
backend/app/scripts/run_gate20d_retrieval_runtime_status_cli.py
docs/checkpoints/Gate 20D Retrieval Runtime Status CLI Surface Build Plan.md
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate20d_retrieval_runtime_status_cli
```

## Expected Validation Output

```text
[gate20d:status-cli] OK
[gate20d:status-cli] text_output=pass
[gate20d:status-cli] json_output=pass
[gate20d:status-cli] invalid_format=fail_closed
[gate20d:status-cli] live_adapter=bm25_authoritative
[gate20d:status-cli] semantic_retrieval_enabled=false
# Retrieval Runtime Operator Status
...
[gate20d] Pipeline complete
[gate20d] Retrieval runtime status CLI exposes BM25-authoritative fail-closed posture
```

## Completion Criteria

Gate 20D is complete when:

1. Text status output renders the Gate 20C operator status.
2. JSON status output renders deterministic structured status.
3. Unsupported output formats fail closed.
4. Local validation passes.
5. PR diff contains only Gate 20D source and checkpoint files.
6. No generated `kbs/` artifacts are committed.

## Next Gate Candidate

Gate 20E — Retrieval Runtime Status CLI Documentation or Integration Hook.
