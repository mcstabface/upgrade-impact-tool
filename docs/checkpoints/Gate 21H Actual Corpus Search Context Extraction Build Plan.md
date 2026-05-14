# Gate 21H Actual Corpus Search Context Extraction Build Plan

## Gate

Gate 21H — Actual Corpus Search Context Extraction Execution

## Purpose

Gate 21H executes the existing KB search-context extraction path after regenerating and validating actual-corpus prerequisites.

This is the first Phase 21 gate that moves beyond readiness checks and writes actual search-context artifacts for the corpus.

## Why This Gate Exists

Gate 21G confirmed the actual corpus can be made ready for search-context extraction:

```text
source_inventory_status=ACTUAL_CORPUS_SOURCE_INVENTORY_EXTRACTED
search_context_readiness_status=ACTUAL_CORPUS_SEARCH_CONTEXT_EXTRACTION_READY
ready_for_search_context_extraction=true
```

Gate 21H runs the existing evidence-map driven extractor once that prerequisite state is true.

## Scope

The extraction reports:

- prerequisite regeneration status
- search-context readiness status
- evidence map path
- output root
- manifest output path
- matched row count
- artifact count
- extraction failure count
- empty text count
- image-bearing artifact count
- highlight-bearing artifact count
- warnings and errors

## Non-Goals

Gate 21H does not:

- build a new extractor
- change the existing search-context artifact schema
- chunk documents
- build embeddings
- build indexes
- run retrieval
- enable semantic vector retrieval
- enable hybrid retrieval
- commit generated `kbs/` reports, manifests, or search-context artifacts

## Files Planned

```text
backend/app/scripts/actual_corpus_search_context_extraction.py
backend/app/scripts/validate_actual_corpus_search_context_extraction.py
backend/app/scripts/run_gate21h_actual_corpus_search_context_extraction.py
docs/checkpoints/Gate 21H Actual Corpus Search Context Extraction Build Plan.md
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate21h_actual_corpus_search_context_extraction
```

## Expected Validation Output

```text
[gate21h:search-context] OK
[gate21h:search-context] missing_prerequisites=blocked
[gate21h:search-context] empty_evidence_map=extracted
[gate21h:search-context] Wrote extraction report: .../kbs/retrieval/kb_actual_corpus_search_context_extraction.v1.json
[gate21h:search-context] status=...
[gate21h:search-context] prerequisite_status=...
[gate21h:search-context] readiness_status=...
[gate21h:search-context] ready_for_search_context_extraction=...
[gate21h:search-context] matched_row_count=...
[gate21h:search-context] artifact_count=...
[gate21h:search-context] extraction_failed_count=...
[gate21h] Pipeline complete
[gate21h] Actual corpus search-context extraction completed
```

The exact counts depend on the local evidence map and extracted PDFs.

## Runtime Artifacts

The runner writes generated local artifacts including:

```text
kbs/manifests/actual_corpus_source_inventory.json
kbs/manifests/kb_search_context_manifest.json
kbs/search_context/
kbs/retrieval/kb_actual_corpus_search_context_extraction.v1.json
```

These generated artifacts should not be committed.

## Completion Criteria

Gate 21H is complete when:

1. Search-context extraction wrapper exists.
2. Validator covers blocked and executable extraction paths.
3. Runner validates and executes extraction against the actual corpus prerequisite set.
4. Local validation passes.
5. PR diff contains only Gate 21H source and checkpoint files.
6. No generated `kbs/` artifacts are committed.

## Next Gate Candidate

Gate 21I — Actual Corpus Search Context Extraction Summary or Demo Query Candidate Capture
