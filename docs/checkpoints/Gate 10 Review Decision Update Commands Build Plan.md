# Gate 10 Review Decision Update Commands Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Review Decision Update Commands  
Status: Initial mutable-review-state slice  
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

Current Gate 9 baseline:

- review manifest schema is `kb_draft_review_manifest.v1`
- review status is `PENDING_REVIEW`
- claim review tasks: 15
- evidence review tasks: 13
- visual review tasks: 13
- unresolved gap tasks: 10
- finalization allowed: false
- reviewer decisions default to `UNSET`
- validator passes with `[gate9:validate] OK`

## Gate 10 Objective

Gate 10 answers this bounded question:

> Can reviewer decisions and gap acknowledgements be updated safely while preserving evidence, visual-review, and finalization controls?

Gate 10 does not add a UI and does not finalize drafts.

It adds controlled CLI mutation paths for the review manifest.

## First Implementation Slice

Added scripts:

| Script | Purpose |
|---|---|
| `backend/app/scripts/update_kb_review_claim_decision.py` | Updates one claim review task decision. |
| `backend/app/scripts/update_kb_review_gap_acknowledgement.py` | Updates one unresolved gap acknowledgement task. |
| `backend/app/scripts/validate_kb_review_state.py` | Validates mutable review state after updates. |
| `backend/app/scripts/run_gate10_kb_review_updates.py` | Runs Gate 10 smoke checks using a copied smoke manifest. |

## Review Update Commands

### Claim decision update

```bash
python -m app.scripts.update_kb_review_claim_decision \
  evidence_group_006 \
  ACCEPT \
  --visual-acknowledged \
  --reviewer "reviewer-id" \
  --notes "Reviewed evidence and visual PFDS content."
```

Allowed decisions:

```text
UNSET
ACCEPT
REJECT
NEEDS_MORE_EVIDENCE
```

Important guard:

- claims citing image-bearing evidence cannot be accepted unless `--visual-acknowledged` is provided.

### Gap acknowledgement update

```bash
python -m app.scripts.update_kb_review_gap_acknowledgement \
  gap_001 \
  ACKNOWLEDGED \
  --reviewer "reviewer-id" \
  --notes "Acknowledged missing PFDS evidence."
```

Allowed acknowledgements:

```text
UNSET
ACKNOWLEDGED
NEEDS_MORE_EVIDENCE
```

## Mutable Review State Validation

Validator:

```bash
python -m app.scripts.validate_kb_review_state
```

Completion preflight mode:

```bash
python -m app.scripts.validate_kb_review_state --require-complete
```

Validation checks:

- manifest type/schema,
- review status is supported,
- finalization remains disabled,
- claim task count matches draft claims,
- claim IDs resolve to draft claims,
- evidence IDs resolve to enriched context,
- accepted evidence-backed claims retain evidence IDs,
- accepted image-bearing claims require visual acknowledgement,
- reviewed decisions set `review_status = REVIEWED`,
- unresolved gap count matches draft gaps,
- gap acknowledgements use allowed values,
- diagnostics match mutable review state.

## Gate 10 Smoke Runner

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate10_kb_review_updates
```

The runner:

1. runs Gate 9 to regenerate the base manifest,
2. validates the initial mutable review state,
3. copies the base manifest to `kbs/review/kb_draft_review_manifest.gate10_smoke.json`,
4. accepts one image-bearing claim with visual acknowledgement,
5. acknowledges one unresolved evidence gap,
6. validates the updated smoke manifest.

The smoke manifest remains generated/ignored.

## Generated Outputs

| Artifact | Purpose |
|---|---|
| `kbs/review/kb_draft_review_manifest.v1.json` | Base pending review manifest from Gate 9. |
| `kbs/review/kb_draft_review_manifest.gate10_smoke.json` | Updated smoke-test review manifest. |
| `kbs/manifests/kb_draft_review_export.md` | Reviewer-facing export from Gate 9. |

Generated review JSON artifacts remain ignored by Git:

```text
kbs/review/
```

## Acceptance Criteria

Gate 10 initial slice is complete when:

1. `python -m app.scripts.run_gate10_kb_review_updates` completes successfully.
2. Initial review state validates with `[gate10:validate] OK`.
3. Updated smoke review state validates with `[gate10:validate] OK`.
4. Accepted image-bearing claim requires and records visual acknowledgement.
5. Gap acknowledgement updates review status and diagnostics.
6. Finalization remains disabled.
7. No UI mutation is introduced.

## Non-Goals

Gate 10 does not:

- expose UI,
- finalize drafts,
- auto-accept claims,
- call an LLM,
- change draft content,
- mutate the committed Markdown export as a source of truth.

## Next Build Steps

### Step 1 — Run Gate 10 locally

```bash
python -m app.scripts.run_gate10_kb_review_updates
```

Expected output includes:

```text
[gate9:validate] OK
[gate10:validate] OK
[gate10:validate] OK
```

### Step 2 — Add Gate 10 completion artifact

After a clean run, add:

```text
docs/checkpoints/Gate 10 Review Decision Update Commands Completion Artifact.md
```

### Step 3 — Next gate selection

Recommended next gate after Gate 10 completion:

**Gate 11 — Review UI Surface**

Gate 11 should expose the stable review manifest/update workflow in the UI.

Do not build UI mutation until the update command contract is clean.

## Notes

Gate 10 is a state-transition safety gate. It proves review decisions can be updated without weakening evidence, visual-review, or gap controls.
