# Retrieval Runtime Status Bundle Runbook

## Purpose

This runbook documents the retrieval runtime status bundle introduced in Gate 20F.

The bundle aggregates the retrieval runtime boundary, runtime health surface, and operator status export into one deterministic status artifact.

## Command

Run from the repository backend directory:

```bash
cd backend
python -m app.scripts.run_gate20f_retrieval_runtime_status_bundle
```

The command validates bundle behavior and writes the current runtime status bundle locally.

## Bundle Artifact

The bundle is written to:

```text
kbs/retrieval/kb_retrieval_runtime_status_bundle.v1.json
```

This is a generated runtime artifact. It should not be committed.

## Healthy Bundle

A healthy bundle reports:

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

## Operator Interpretation

| Field | Expected Healthy Value | Meaning |
|---|---|---|
| `status` | `RETRIEVAL_RUNTIME_STATUS_BUNDLE_READY` | End-to-end runtime status bundle is healthy |
| `boundary_status` | `RETRIEVAL_RUNTIME_BOUNDARY_READY` | Runtime adapter boundary accepted BM25-authoritative state |
| `health_status` | `RETRIEVAL_RUNTIME_HEALTHY` | Runtime health checks passed |
| `operator_action_required` | `none` | No operator intervention required |
| `live_adapter` | `bm25_authoritative` | BM25 remains the live retrieval adapter |
| `bm25_authoritative` | `true` | BM25 remains authoritative |
| `semantic_retrieval_enabled` | `false` | Semantic vector retrieval is not enabled |
| `hybrid_merge_enabled` | `false` | Hybrid merge is not enabled |
| `fail_closed` | `true` | Unsafe state refuses activation |

## Unhealthy Bundle

If the bundle reports:

```text
status=RETRIEVAL_RUNTIME_STATUS_BUNDLE_UNHEALTHY
```

or:

```text
operator_action_required=investigate_runtime_health
```

then operator use should stop until the unhealthy boundary, health, or operator-status condition is reviewed.

Known unhealthy causes include:

```text
semantic_retrieval_enabled=true
fail_closed=false
boundary_status not RETRIEVAL_RUNTIME_BOUNDARY_READY
health_status not RETRIEVAL_RUNTIME_HEALTHY
operator_action_required not none
```

## Generated Runtime Artifacts

The bundle runner may write generated artifacts under:

```text
kbs/retrieval/
```

These are local runtime artifacts and should not be committed.

For cleanup:

```bash
rm -rf kbs/retrieval
```

## Diff Hygiene

After running validation locally, the only expected untracked output is:

```text
?? kbs/retrieval/
```

Do not commit it.

## Boundary Summary

The status bundle is a reporting artifact. It does not enable semantic retrieval, hybrid merge, vector authority, or any new retrieval adapter.
