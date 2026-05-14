# Gate 21D Actual Corpus Ingestion Dry Run Build Plan

## Gate

Gate 21D — Actual Corpus Ingestion Dry Run

## Purpose

Gate 21D adds a read-only ingestion dry run for the actual customer corpus rooted at:

```text
kbs/raw
```

The dry run uses the existing KB source inventory manifest path to assess whether the actual corpus has the expected HTML sources and PDF portfolio files before running a real ingestion pass.

## Why This Gate Exists

Gate 21C confirmed that the actual corpus exists and contains files. Gate 21D determines whether those files are structurally ready for the existing KB source inventory ingestion path.

## Scope

The dry run reports:

- whether `kbs/raw` exists
- HTML source count
- PDF portfolio count
- KB document count
- missing referenced portfolio count
- unreferenced portfolio count
- dry-run readiness checks
- warnings and recommended next steps

## Non-Goals

Gate 21D does not:

- mutate corpus files
- write the production source inventory manifest
- extract search context
- chunk documents
- build embeddings
- build indexes
- run retrieval
- enable semantic vector retrieval
- enable hybrid retrieval
- commit generated `kbs/` reports

## Files Planned

```text
backend/app/scripts/actual_corpus_ingestion_dry_run.py
backend/app/scripts/validate_actual_corpus_ingestion_dry_run.py
backend/app/scripts/run_gate21d_actual_corpus_ingestion_dry_run.py
docs/checkpoints/Gate 21D Actual Corpus Ingestion Dry Run Build Plan.md
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate21d_actual_corpus_ingestion_dry_run
```

## Expected Validation Output

```text
[gate21d:ingestion-dry-run] OK
[gate21d:ingestion-dry-run] missing_root=not_ready
[gate21d:ingestion-dry-run] empty_root=not_ready
[gate21d:ingestion-dry-run] populated_root=ready
[gate21d:ingestion-dry-run] Wrote ingestion dry-run report: .../kbs/retrieval/kb_actual_corpus_ingestion_dry_run.v1.json
[gate21d:ingestion-dry-run] status=...
[gate21d:ingestion-dry-run] source_root=kbs/raw
[gate21d:ingestion-dry-run] source_root_exists=true
[gate21d] Pipeline complete
[gate21d] Actual corpus ingestion dry run completed for kbs/raw
```

The exact status depends on the local corpus structure.

## Runtime Artifact

The runner writes a generated local report:

```text
kbs/retrieval/kb_actual_corpus_ingestion_dry_run.v1.json
```

This report is a runtime artifact and should not be committed.

## Completion Criteria

Gate 21D is complete when:

1. Ingestion dry-run reporter exists.
2. Validator covers missing, empty, and populated corpus roots.
3. Runner validates and reports against `kbs/raw`.
4. Local validation passes.
5. PR diff contains only Gate 21D source and checkpoint files.
6. No generated `kbs/` artifacts are committed.

## Next Gate Candidate

Gate 21E — Actual Corpus Source Inventory Extraction or Demo Query Candidate Capture
