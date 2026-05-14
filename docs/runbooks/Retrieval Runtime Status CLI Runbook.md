# Retrieval Runtime Status CLI Runbook

## Purpose

This runbook documents the retrieval runtime status CLI introduced in Gate 20D.

The CLI gives an operator-readable view of the retrieval runtime posture while preserving the BM25-authoritative, fail-closed boundary established by Gates 20A through 20D.

## Command

Run from the repository backend directory:

```bash
cd backend
python -m app.scripts.retrieval_runtime_status_cli
```

The default output format is text.

## JSON Output

For automation or structured inspection:

```bash
cd backend
python -m app.scripts.retrieval_runtime_status_cli --format json
```

## Healthy Status

A healthy retrieval runtime reports:

```text
status=RETRIEVAL_RUNTIME_HEALTHY
live_adapter=bm25_authoritative
bm25_authoritative=true
semantic_retrieval_enabled=false
hybrid_merge_enabled=false
fail_closed=true
action_required=none
```

## Operator Interpretation

| Field | Expected Healthy Value | Meaning |
|---|---|---|
| `status` | `RETRIEVAL_RUNTIME_HEALTHY` | Runtime boundary and health checks passed |
| `live_adapter` | `bm25_authoritative` | BM25 remains the live retrieval adapter |
| `bm25_authoritative` | `true` | BM25 remains authoritative |
| `semantic_retrieval_enabled` | `false` | Semantic vector retrieval is not enabled |
| `hybrid_merge_enabled` | `false` | Hybrid merge is not enabled |
| `fail_closed` | `true` | Invalid or unsafe runtime state fails closed |
| `action_required` | `none` | No operator intervention required |

## Unhealthy Status

If the CLI reports:

```text
action_required=investigate_runtime_health
```

then operator use should stop until the runtime health failure is reviewed.

Known unhealthy causes include:

```text
semantic_retrieval_enabled=true
fail_closed=false
live_adapter not bm25_authoritative
selected_adapter not bm25_authoritative
```

## Generated Runtime Artifacts

The CLI may bootstrap local runtime reports under:

```text
kbs/retrieval/
```

These generated reports are local runtime artifacts and should not be committed.

For cleanup:

```bash
rm -rf kbs/retrieval
```

## Validation Command

To validate the CLI behavior:

```bash
cd backend
python -m app.scripts.run_gate20d_retrieval_runtime_status_cli
```

Expected validation markers include:

```text
[gate20d:status-cli] OK
[gate20d:status-cli] text_output=pass
[gate20d:status-cli] json_output=pass
[gate20d:status-cli] invalid_format=fail_closed
[gate20d:status-cli] live_adapter=bm25_authoritative
[gate20d:status-cli] semantic_retrieval_enabled=false
```

## Boundary Summary

This CLI is read-only from an operator perspective. It reports retrieval runtime posture; it does not enable semantic retrieval, hybrid merge, vector authority, or any new retrieval adapter.
