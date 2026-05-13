# Gate 12 UI Mutation Bridge Build Plan

System: Upgrade Impact Analysis Tool  
Phase: UI Mutation Bridge to Gate 10 Commands  
Status: Initial bridge/audit smoke slice  
Generated: 2026-05-13

## Starting Point

Gate 1 completed KB source extraction and PFDS evidence mapping.

Gate 2 completed matched PFDS source text extraction and deterministic chunking.

Gate 3 completed deterministic lexical retrieval over PFDS chunks.

Gate 4 completed retrieval diagnostics and controls.

Gate 5 completed deterministic BM25 ranking and retrieval evaluation.

Gate 6 completed evidence-only impact context assembly.

Gate 7 completed impact context enrichment and draft skeleton.

Gate 8 completed constrained citation-bound impact draft generation.

Gate 9 completed draft review workflow and reviewer export.

Gate 10 completed review decision update commands.

Gate 11 completed read-only review UI surface.

Current Gate 11 baseline:

- read-only static review surface is generated
- review status is `PENDING_REVIEW`
- claim tasks: 15
- evidence review tasks: 13
- visual review tasks: 13
- unresolved gap tasks: 10
- finalization allowed: false
- surface includes claim cards, evidence lineage, visual-review flags, and gap cards
- surface contains read-only reviewer fields
- validator passes with `[gate11:validate] OK`

## Gate 12 Objective

Gate 12 answers this bounded question:

> Can review mutations be applied through a controlled bridge that uses Gate 10 update logic, immediately validates state, regenerates reviewer artifacts, and records an audit trail?

Gate 12 still does not add browser-side mutation.

It creates the mutation bridge that future UI actions must call.

## First Implementation Slice

Added scripts:

| Script | Purpose |
|---|---|
| `backend/app/scripts/apply_kb_review_update.py` | Applies a claim or gap review update through Gate 10 update functions, records audit event, validates state, and regenerates review artifacts. |
| `backend/app/scripts/validate_kb_review_audit_trail.py` | Validates review audit trail structure and state deltas. |
| `backend/app/scripts/run_gate12_kb_review_mutation_bridge.py` | Runs bridge smoke checks against a copied review manifest. |

## Mutation Bridge Contract

The bridge script supports two actions:

```bash
python -m app.scripts.apply_kb_review_update \
  --reviewer "reviewer-id" \
  --notes "Reviewed evidence and visual PFDS content." \
  claim evidence_group_006 ACCEPT --visual-acknowledged
```

```bash
python -m app.scripts.apply_kb_review_update \
  --reviewer "reviewer-id" \
  --notes "Acknowledged missing PFDS evidence." \
  gap gap_001 ACKNOWLEDGED
```

For every mutation, the bridge must:

1. load the review manifest,
2. capture previous target state,
3. call the Gate 10 update function,
4. capture new target state,
5. append an audit event,
6. write the manifest,
7. run `validate_kb_review_state`,
8. regenerate Markdown review export,
9. regenerate static review surface,
10. run `validate_kb_draft_review_surface`.

## Audit Event Contract

Each audit event includes:

- event ID,
- timestamp UTC,
- action type,
- target ID,
- reviewer,
- previous state,
- new state.

Supported action types:

```text
CLAIM_DECISION_UPDATE
GAP_ACKNOWLEDGEMENT_UPDATE
```

Audit validation checks:

- at least the expected number of events exists,
- event IDs are unique,
- reviewer is explicit,
- action type is supported,
- previous/new state are objects,
- previous/new state differ,
- claim decision events change `reviewer_decision`,
- gap acknowledgement events change `acknowledgement_status`,
- diagnostics audit-event count matches the event list.

## Gate 12 Smoke Runner

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate12_kb_review_mutation_bridge
```

The runner:

1. runs Gate 11 to regenerate the base read-only review surface,
2. copies the base manifest to `kbs/review/kb_draft_review_manifest.gate12_bridge.json`,
3. applies one claim decision update through the bridge,
4. applies one gap acknowledgement through the bridge,
5. validates mutable review state,
6. validates audit trail with at least two events,
7. validates the regenerated bridged review surface.

## Generated Outputs

| Artifact | Purpose |
|---|---|
| `kbs/review/kb_draft_review_manifest.gate12_bridge.json` | Smoke-test bridged review manifest with audit events. |
| `kbs/manifests/kb_draft_review_export.gate12_bridge.md` | Smoke-test reviewer export regenerated from bridged manifest. |
| `kbs/manifests/kb_draft_review_surface.gate12_bridge.html` | Smoke-test static surface regenerated from bridged manifest. |

Generated review JSON remains ignored by Git. Smoke Markdown/HTML outputs may be committed intentionally only if desired, but are primarily local validation artifacts.

## Acceptance Criteria

Gate 12 initial slice is complete when:

1. `python -m app.scripts.run_gate12_kb_review_mutation_bridge` completes successfully.
2. Gate 11 base pipeline passes with `[gate11:validate] OK`.
3. The bridge applies one claim decision update.
4. The bridge applies one gap acknowledgement update.
5. Mutable review state validates with `[gate10:validate] OK`.
6. Audit trail validates with `[gate12:audit] OK`.
7. Regenerated bridged surface validates with `[gate11:validate] OK`.
8. Audit trail contains at least two events.
9. Finalization remains disabled.
10. No browser mutation is introduced.

## Non-Goals

Gate 12 does not:

- add browser-side mutation,
- expose a live API endpoint,
- finalize drafts,
- auto-accept claims,
- call an LLM,
- change draft content,
- bypass Gate 10 validators.

## Next Build Steps

### Step 1 — Run Gate 12 locally

```bash
python -m app.scripts.run_gate12_kb_review_mutation_bridge
```

Expected validation output includes:

```text
[gate11:validate] OK
[gate10:validate] OK
[gate12:audit] OK
[gate11:validate] OK
```

### Step 2 — Add Gate 12 completion artifact

After a clean run, add:

```text
docs/checkpoints/Gate 12 UI Mutation Bridge Completion Artifact.md
```

### Step 3 — Next gate selection

Recommended next gate after Gate 12 completion:

**Gate 13 — Live Review API or Controlled UI Mutation**

Only after Gate 12 bridge validation is clean should a live endpoint or browser action call the bridge. Mutation must still call `validate_kb_review_state` immediately after update and regenerate reviewer artifacts.

## Notes

Gate 12 is not a UI feature in the flashy sense. It is the mutation adapter that future UI code must use so it cannot conveniently forget the safety invariants. Tedious. Necessary. The usual bargain.
