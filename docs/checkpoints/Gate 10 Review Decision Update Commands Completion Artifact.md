# Gate 10 Review Decision Update Commands Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: Review Decision Update Commands  
Status: Complete for current sample corpus  
Generated: 2026-05-13

## Purpose

This checkpoint captures the completed state of Gate 10 for the KB ingestion/customization phase.

Gate 10 answered this bounded question:

> Can reviewer decisions and gap acknowledgements be updated safely while preserving evidence, visual-review, and finalization controls?

For the current sample corpus, the answer is yes.

Gate 10 does not expose a UI, finalize drafts, auto-accept claims, call an LLM, or change draft content. It adds controlled CLI mutation paths and mutable-state validation for the review manifest.

## Source Baseline

Gate 10 starts from Gate 9 draft review workflow and reviewer export.

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

## Gate 10 Pipeline

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate10_kb_review_updates
```

Dry run:

```bash
python -m app.scripts.run_gate10_kb_review_updates --dry-run
```

The orchestrator runs these modules in order:

1. `app.scripts.run_gate9_kb_draft_review`
2. `app.scripts.validate_kb_review_state` against the base manifest
3. copy base manifest to `kbs/review/kb_draft_review_manifest.gate10_smoke.json`
4. `app.scripts.update_kb_review_claim_decision` against the smoke manifest
5. `app.scripts.update_kb_review_gap_acknowledgement` against the smoke manifest
6. `app.scripts.validate_kb_review_state` against the updated smoke manifest

## Generated Artifacts

| Artifact | Purpose |
|---|---|
| `kbs/review/kb_draft_review_manifest.v1.json` | Base pending review manifest from Gate 9 |
| `kbs/review/kb_draft_review_manifest.gate10_smoke.json` | Smoke-test manifest with one accepted claim and one acknowledged gap |
| `kbs/manifests/kb_draft_review_export.md` | Reviewer-facing base review export |

Generated review JSON artifacts remain ignored by Git:

```text
kbs/review/
```

The Markdown export remains reviewable and may be committed intentionally.

## Latest Verified Pipeline Output

Local clean run completed successfully with:

```text
python -m app.scripts.run_gate10_kb_review_updates
```

Validation:

```text
[gate9:validate] OK
[gate10:validate] OK
[gate10:validate] OK
```

The first Gate 10 validation confirms the fresh Gate 9 base manifest is valid as mutable review state.

The second Gate 10 validation confirms the smoke-updated manifest is valid after:

- accepting one image-bearing evidence claim with visual acknowledgement,
- acknowledging one unresolved evidence gap.

## Base Review Export State

The committed reviewer export remains the base pending review state, not the smoke-mutated state.

Current base export counts:

- Artifact type: `kb_draft_review_manifest`
- Schema version: `kb_draft_review_manifest.v1`
- Review status: `PENDING_REVIEW`
- Claim review tasks: 15
- Evidence review tasks: 13
- Visual review tasks: 13
- Unresolved gap tasks: 10
- Finalization allowed: `False`

This is intentional. The smoke manifest validates update behavior without changing the canonical generated review export.

## Claim Decision Update Command

Script:

```text
backend/app/scripts/update_kb_review_claim_decision.py
```

Allowed decisions:

```text
UNSET
ACCEPT
REJECT
NEEDS_MORE_EVIDENCE
```

Example:

```bash
python -m app.scripts.update_kb_review_claim_decision \
  evidence_group_006 \
  ACCEPT \
  --visual-acknowledged \
  --reviewer "reviewer-id" \
  --notes "Reviewed evidence and visual PFDS content."
```

Important guard:

```text
ACCEPT + image-bearing evidence requires --visual-acknowledged
```

When a claim decision is set to `ACCEPT`, `REJECT`, or `NEEDS_MORE_EVIDENCE`, the claim task review status becomes:

```text
REVIEWED
```

When a claim decision is reset to `UNSET`, the claim task review status becomes:

```text
PENDING_REVIEW
```

## Gap Acknowledgement Update Command

Script:

```text
backend/app/scripts/update_kb_review_gap_acknowledgement.py
```

Allowed acknowledgement states:

```text
UNSET
ACKNOWLEDGED
NEEDS_MORE_EVIDENCE
```

Example:

```bash
python -m app.scripts.update_kb_review_gap_acknowledgement \
  gap_001 \
  ACKNOWLEDGED \
  --reviewer "reviewer-id" \
  --notes "Acknowledged missing PFDS evidence."
```

When acknowledgement is set to `ACKNOWLEDGED` or `NEEDS_MORE_EVIDENCE`, the gap task review status becomes:

```text
ACKNOWLEDGED
```

When acknowledgement is reset to `UNSET`, the gap task review status becomes:

```text
PENDING_ACKNOWLEDGEMENT
```

## Mutable Review State Validator

Script:

```text
backend/app/scripts/validate_kb_review_state.py
```

Standard validation:

```bash
python -m app.scripts.validate_kb_review_state
```

Completion preflight:

```bash
python -m app.scripts.validate_kb_review_state --require-complete
```

Standard validation permits partial review progress. Completion preflight requires all claim decisions and unresolved-gap acknowledgements to be set.

Validator checks:

- manifest artifact type and schema,
- supported review status,
- finalization remains disabled,
- claim task count matches draft claim count,
- claim IDs resolve to draft claims,
- no duplicate claim tasks,
- evidence IDs resolve to enriched context,
- accepted evidence-backed claims retain evidence IDs,
- accepted image-bearing claims require visual acknowledgement,
- reviewed decisions set `review_status = REVIEWED`,
- unresolved gap count matches draft gap count,
- gap acknowledgements use allowed values,
- diagnostics match mutable review state.

## Gate 10 Smoke Update

The smoke runner copies the base review manifest to:

```text
kbs/review/kb_draft_review_manifest.gate10_smoke.json
```

Then it applies:

```bash
python -m app.scripts.update_kb_review_claim_decision \
  evidence_group_006 \
  ACCEPT \
  --manifest kbs/review/kb_draft_review_manifest.gate10_smoke.json \
  --output kbs/review/kb_draft_review_manifest.gate10_smoke.json \
  --reviewer GATE10_SMOKE \
  --notes "Smoke-test acceptance with visual acknowledgement." \
  --visual-acknowledged
```

and:

```bash
python -m app.scripts.update_kb_review_gap_acknowledgement \
  gap_001 \
  ACKNOWLEDGED \
  --manifest kbs/review/kb_draft_review_manifest.gate10_smoke.json \
  --output kbs/review/kb_draft_review_manifest.gate10_smoke.json \
  --reviewer GATE10_SMOKE \
  --notes "Smoke-test unresolved gap acknowledgement."
```

The updated smoke manifest then validates with:

```text
[gate10:validate] OK
```

## Key Code Added During Gate 10

| Script / Artifact | Purpose |
|---|---|
| `backend/app/scripts/update_kb_review_claim_decision.py` | Updates one claim review decision with visual-review guard |
| `backend/app/scripts/update_kb_review_gap_acknowledgement.py` | Updates one unresolved gap acknowledgement |
| `backend/app/scripts/validate_kb_review_state.py` | Validates mutable review state and optional completion preflight |
| `backend/app/scripts/run_gate10_kb_review_updates.py` | Runs review update smoke checks against a copied manifest |
| `docs/checkpoints/Gate 10 Review Decision Update Commands Build Plan.md` | Captures Gate 10 build plan and acceptance criteria |

## Validation Coverage

Gate 10 validates that:

- review state can move from pending to in-review,
- reviewer decisions use allowed values,
- gap acknowledgements use allowed values,
- accepted image-bearing claims cannot bypass visual acknowledgement,
- diagnostics are recomputed after updates,
- partial review state remains valid,
- completion preflight can require every decision and acknowledgement,
- finalization remains blocked.

## What This Proves

Gate 10 proves that the project can now:

- mutate review state safely from CLI commands,
- accept/reject/mark claims as needing more evidence,
- acknowledge unresolved evidence gaps,
- enforce visual-review acknowledgement for accepted image-bearing evidence,
- validate partially reviewed state,
- run stricter completion validation when needed,
- keep UI work downstream of a stable artifact contract.

## Known Limitations

Gate 10 remains CLI/artifact-only.

Known limitations:

- It does not expose review decisions in a web UI yet.
- It does not generate a post-update Markdown export for the smoke manifest.
- It does not finalize drafts.
- It does not support bulk review updates yet.
- It does not persist reviewer identity beyond manifest fields.
- It does not call an LLM.

These limitations are acceptable for Gate 10. They define the next gate.

## Recommended Next Gate

Recommended next gate:

**Gate 11 — Review UI Surface**

Gate 11 should expose the stable review manifest/update workflow in the UI.

Proposed Gate 11 sequence:

1. Add backend read endpoint or local service function for review manifest/export data.
2. Add UI page or panel that lists:
   - draft sections,
   - claims,
   - claim decisions,
   - evidence IDs,
   - visual-review flags,
   - unresolved gaps.
3. Initially keep UI read-only if mutation plumbing is not ready.
4. Add mutation only by calling the Gate 10 update contract.
5. Preserve finalization-disabled state until a later explicit finalization gate.

Do not build UI mutation that bypasses Gate 10 commands or state validation.

## Recommended Next Chat Starting Point

Use this prompt to continue in a new chat:

```text
We are continuing work on the Upgrade Impact Analysis Tool.

Gate 1 completed KB source extraction and PFDS evidence mapping.
Gate 2 completed KB PFDS source text extraction and deterministic chunking.
Gate 3 completed KB PFDS lexical retrieval index and query.
Gate 4 completed retrieval diagnostics and controls.
Gate 5 completed deterministic BM25 ranking and retrieval evaluation.
Gate 6 completed evidence-only impact context assembly.
Gate 7 completed impact context enrichment and draft skeleton.
Gate 8 completed constrained citation-bound impact draft generation.
Gate 9 completed draft review workflow and reviewer export.
Gate 10 completed review decision update commands.

Use this repo as source of truth:
mcstabface/upgrade-impact-tool

Start from these docs/artifacts:
- docs/checkpoints/Gate 1 KB Source Extraction Completion Artifact.md
- docs/checkpoints/Gate 2 KB Search Context Completion Artifact.md
- docs/checkpoints/Gate 3 KB PFDS Retrieval Completion Artifact.md
- docs/checkpoints/Gate 4 KB Retrieval Diagnostics Completion Artifact.md
- docs/checkpoints/Gate 5 BM25 Ranking Evaluation Completion Artifact.md
- docs/checkpoints/Gate 6 Impact Context Assembly Completion Artifact.md
- docs/checkpoints/Gate 7 Impact Context Enrichment Completion Artifact.md
- docs/checkpoints/Gate 8 Constrained Impact Draft Completion Artifact.md
- docs/checkpoints/Gate 9 Draft Review Workflow Completion Artifact.md
- docs/checkpoints/Gate 10 Review Decision Update Commands Completion Artifact.md
- kbs/manifests/kb_draft_review_export.md
- backend/app/scripts/run_gate10_kb_review_updates.py
- backend/app/scripts/update_kb_review_claim_decision.py
- backend/app/scripts/update_kb_review_gap_acknowledgement.py
- backend/app/scripts/validate_kb_review_state.py

Current Gate 10 status:
- claim decision updates are supported
- gap acknowledgement updates are supported
- mutable review state validation is supported
- accepted image-bearing claims require visual acknowledgement
- partial review state validation passes
- completion preflight validation is available with `--require-complete`
- finalization remains disabled
- smoke runner passes with `[gate10:validate] OK` before and after updates

The Gate 10 smoke pipeline runs successfully with:
python -m app.scripts.run_gate10_kb_review_updates

Next recommended gate is Gate 11: Review UI Surface.

Please review the repo and produce the next concrete build plan and first patches for Gate 11.
Be specific, repo-grounded, and provide exact patch contents.
```

## Completion Status

Gate 10 is complete for the current source corpus.

The next work should begin from this checkpoint, not from memory.
