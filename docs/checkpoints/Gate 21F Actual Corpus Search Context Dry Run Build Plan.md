# Gate 21F Actual Corpus Search Context Dry Run Build Plan

## Gate

Gate 21F — Actual Corpus Search Context Dry Run

## Purpose

Gate 21F checks whether the actual customer corpus is ready for search-context extraction.

This gate does not run extraction. It verifies that the prerequisite artifacts required by the existing search-context extraction path are present and reports what is missing.

## Why This Gate Exists

Gate 21E extracted the actual corpus source inventory. Search-context extraction requires downstream artifacts beyond the source inventory:

```text
actual corpus source inventory
portfolio extraction manifest
KB fix rows manifest
KB evidence map
```

The existing search-context extractor consumes an evidence map, so this gate prevents us from pretending search-context extraction is ready before its prerequisites exist.

## Scope

The dry run reports:

- actual corpus source inventory presence
- portfolio extraction manifest presence
- KB fix rows manifest presence
- KB evidence map presence
- expected search-context output root
- expected search-context manifest path
- readiness status
- missing prerequisite list
- recommended next steps

## Non-Goals

Gate 21F does not:

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
- commit generated `kbs/` reports

## Files Planned

```text
backend/app/scripts/actual_corpus_search_context_dry_run.py
backend/app/scripts/validate_actual_corpus_search_context_dry_run.py
backend/app/scripts/run_gate21f_actual_corpus_search_context_dry_run.py
docs/checkpoints/Gate 21F Actual Corpus Search Context Dry Run Build Plan.md
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate21f_actual_corpus_search_context_dry_run
```

## Expected Validation Output

```text
[gate21f:search-context-dry-run] OK
[gate21f:search-context-dry-run] missing_prerequisites=not_ready
[gate21f:search-context-dry-run] all_prerequisites=ready
[gate21f:search-context-dry-run] Wrote dry-run report: .../kbs/retrieval/kb_actual_corpus_search_context_dry_run.v1.json
[gate21f:search-context-dry-run] status=...
[gate21f:search-context-dry-run] ready_for_search_context_extraction=...
[gate21f:search-context-dry-run] missing_prerequisite_count=...
[gate21f] Pipeline complete
[gate21f] Actual corpus search-context extraction dry run completed
```

The exact readiness status depends on which local generated prerequisites are present.

## Runtime Artifact

The runner writes a generated local report:

```text
kbs/retrieval/kb_actual_corpus_search_context_dry_run.v1.json
```

This report is a runtime artifact and should not be committed.

## Completion Criteria

Gate 21F is complete when:

1. Search-context prerequisite dry-run reporter exists.
2. Validator covers missing and present prerequisites.
3. Runner validates and reports local readiness.
4. Local validation passes.
5. PR diff contains only Gate 21F source and checkpoint files.
6. No generated `kbs/` artifacts are committed.

## Next Gate Candidate

Gate 21G — Actual Corpus Portfolio Extraction and Fix Row Prerequisite Generation
