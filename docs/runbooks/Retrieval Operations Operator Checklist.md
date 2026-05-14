# Retrieval Operations Operator Checklist

## Purpose

This checklist packages the retrieval runtime status surfaces completed in Phase 20 into a repeatable operator workflow.

It is intended for local validation, pre-merge runtime gate checks, and demo-readiness review.

## Standing Rule

```text
Documentation-only change: no runtime test required.
Runtime/code change: provide a pull-and-run script before merge.
```

## Pre-Run Cleanup

Before validating retrieval runtime status locally, remove generated runtime reports if they are not needed:

```bash
cd /home/stabby/Documents/upgrade-impact-tool
rm -rf kbs/retrieval
```

## Update Local Main

```bash
cd /home/stabby/Documents/upgrade-impact-tool
git fetch origin
git checkout main
git pull --ff-only origin main
git status --short
```

Expected clean result:

```text
(no output)
```

## Status CLI Check

Run from the backend directory:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
python -m app.scripts.run_gate20d_retrieval_runtime_status_cli
```

Expected healthy markers:

```text
[gate20d:status-cli] OK
[gate20d:status-cli] text_output=pass
[gate20d:status-cli] json_output=pass
[gate20d:status-cli] invalid_format=fail_closed
[gate20d:status-cli] live_adapter=bm25_authoritative
[gate20d:status-cli] semantic_retrieval_enabled=false
[gate20d] Pipeline complete
```

## Status Bundle Check

Run from the backend directory:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
python -m app.scripts.run_gate20f_retrieval_runtime_status_bundle
```

Expected healthy markers:

```text
[gate20f:status-bundle] OK
[gate20f:status-bundle] healthy_bundle=ready
[gate20f:status-bundle] semantic_enabled=unhealthy
[gate20f:status-bundle] fail_open=unhealthy
[gate20f:status-bundle] live_adapter=bm25_authoritative
[gate20f:status-bundle] semantic_retrieval_enabled=false
[gate20f] Pipeline complete
```

## Required Healthy Runtime Posture

```text
live_adapter=bm25_authoritative
selected_adapter=bm25_authoritative
bm25_authoritative=true
semantic_retrieval_enabled=false
hybrid_merge_enabled=false
fail_closed=true
operator_action_required=none
```

## Diff Hygiene After Runtime Checks

Runtime checks may generate local reports under:

```text
kbs/retrieval/
```

This is expected. Do not commit these generated artifacts.

Cleanup command:

```bash
cd /home/stabby/Documents/upgrade-impact-tool
rm -rf kbs/retrieval
```

Final check:

```bash
git status --short
```

Expected clean result:

```text
(no output)
```

## Pre-Merge Checklist For Runtime Gates

For runtime/code gates, confirm:

```text
[ ] Pull-and-run script was provided
[ ] Local validation output was pasted back
[ ] PR diff contains only intended source/checkpoint files
[ ] No generated kbs/ artifacts are committed
[ ] Completion artifact includes local validation output
```

## Pre-Merge Checklist For Documentation Gates

For documentation-only gates, confirm:

```text
[ ] PR diff contains only documentation/checkpoint files
[ ] No runtime test was required
[ ] No generated kbs/ artifacts are committed
[ ] Completion artifact states documentation-only status
```

## Stop Conditions

Stop and investigate if any of the following appear:

```text
semantic_retrieval_enabled=true
hybrid_merge_enabled=true
bm25_authoritative=false
fail_closed=false
operator_action_required=investigate_runtime_health
status=RETRIEVAL_RUNTIME_STATUS_BUNDLE_UNHEALTHY
```

## Operator Summary

The retrieval runtime is acceptable for operator use only when BM25 remains authoritative, semantic retrieval remains disabled, hybrid merge remains disabled, and fail-closed posture remains true.
