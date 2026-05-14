# Gate 21G Actual Corpus Prerequisite Regeneration Build Plan

## Gate

Gate 21G — Actual Corpus Prerequisite Regeneration

## Purpose

Gate 21G regenerates the actual-corpus source inventory and immediately reruns the search-context prerequisite readiness check.

The goal is to move the actual corpus from `not ready` to `ready` for search-context extraction when all downstream prerequisite manifests are present.

## Why This Gate Exists

Gate 21F correctly reported search-context extraction was not ready because the generated actual-corpus source inventory was missing locally:

```text
kbs/manifests/actual_corpus_source_inventory.json
```

Gate 21G regenerates that source inventory and checks readiness again.

## Scope

The regeneration reports:

- source inventory extraction status
- search-context readiness status
- actual-corpus source inventory path
- HTML source count
- portfolio file count
- KB document count
- missing portfolio count
- unreferenced portfolio count
- missing downstream prerequisites

## Non-Goals

Gate 21G does not:

- extract search context
- extract portfolio attachments
- extract KB fix rows
- build the KB evidence map
- chunk documents
- build embeddings
- build indexes
- run retrieval
- enable semantic vector retrieval
- enable hybrid retrieval
- commit generated `kbs/` reports or manifests

## Files Planned

```text
backend/app/scripts/actual_corpus_prerequisite_regeneration.py
backend/app/scripts/validate_actual_corpus_prerequisite_regeneration.py
backend/app/scripts/run_gate21g_actual_corpus_prerequisite_regeneration.py
docs/checkpoints/Gate 21G Actual Corpus Prerequisite Regeneration Build Plan.md
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate21g_actual_corpus_prerequisite_regeneration
```

## Expected Validation Output

```text
[gate21g:prereq-regen] OK
[gate21g:prereq-regen] all_prerequisites=ready
[gate21g:prereq-regen] missing_downstream_prerequisite=blocked
[gate21g:prereq-regen] Wrote prerequisite regeneration report: .../kbs/retrieval/kb_actual_corpus_prerequisite_regeneration.v1.json
[gate21g:prereq-regen] status=...
[gate21g:prereq-regen] source_inventory_status=...
[gate21g:prereq-regen] search_context_readiness_status=...
[gate21g:prereq-regen] ready_for_search_context_extraction=...
[gate21g] Pipeline complete
[gate21g] Actual corpus prerequisite regeneration completed
```

The exact readiness status depends on whether local downstream manifests exist.

## Runtime Artifacts

The runner writes generated local artifacts:

```text
kbs/manifests/actual_corpus_source_inventory.json
kbs/retrieval/kb_actual_corpus_prerequisite_regeneration.v1.json
```

These generated artifacts should not be committed.

## Completion Criteria

Gate 21G is complete when:

1. Prerequisite regeneration reporter exists.
2. Validator covers ready and blocked downstream-prerequisite states.
3. Runner validates, regenerates actual-corpus source inventory, and checks readiness.
4. Local validation passes.
5. PR diff contains only Gate 21G source and checkpoint files.
6. No generated `kbs/` artifacts are committed.

## Next Gate Candidate

Gate 21H — Actual Corpus Search Context Extraction Execution
