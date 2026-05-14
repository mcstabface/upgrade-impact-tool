# Gate 21I Actual Corpus Search Context Summary Build Plan

## Gate

Gate 21I — Actual Corpus Search Context Summary

## Purpose

Gate 21I generates a compact demo-readiness summary from the actual corpus search-context manifest.

The gate reruns the actual search-context extraction path, reads the generated manifest, and emits a summary report with corpus-level extraction metrics and candidate artifacts for demo query preparation.

## Why This Gate Exists

Gate 21H confirmed that the actual corpus can produce search-context artifacts:

```text
matched_row_count=179
artifact_count=179
extraction_failed_count=0
empty_text_count=0
```

Gate 21I packages that generated manifest into a concise report suitable for deciding which evidence artifacts and query themes to show to the customer.

## Scope

The summary reports:

- extraction status
- manifest path
- output root
- matched row count
- artifact count
- extraction failure count
- empty text count
- image-bearing artifact count
- highlight-bearing artifact count
- total extracted characters
- total extracted pages
- average characters per artifact
- top demo candidate artifacts by extracted character count

## Non-Goals

Gate 21I does not:

- alter search-context extraction behavior
- change artifact schemas
- chunk documents
- build embeddings
- build indexes
- run retrieval
- synthesize customer answers
- enable semantic vector retrieval
- enable hybrid retrieval
- commit generated `kbs/` reports, manifests, or search-context artifacts

## Files Planned

```text
backend/app/scripts/actual_corpus_search_context_summary.py
backend/app/scripts/validate_actual_corpus_search_context_summary.py
backend/app/scripts/run_gate21i_actual_corpus_search_context_summary.py
docs/checkpoints/Gate 21I Actual Corpus Search Context Summary Build Plan.md
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate21i_actual_corpus_search_context_summary
```

## Expected Validation Output

```text
[gate21i:search-context-summary] OK
[gate21i:search-context-summary] missing_manifest=blocked
[gate21i:search-context-summary] populated_manifest=summary_ready
[gate21i:search-context-summary] Wrote summary report: .../kbs/retrieval/kb_actual_corpus_search_context_summary.v1.json
[gate21i:search-context-summary] status=...
[gate21i:search-context-summary] extraction_status=...
[gate21i:search-context-summary] matched_row_count=...
[gate21i:search-context-summary] artifact_count=...
[gate21i:search-context-summary] extraction_failed_count=...
[gate21i:search-context-summary] empty_text_count=...
[gate21i:search-context-summary] total_char_count=...
[gate21i:search-context-summary] total_page_count=...
[gate21i:search-context-summary] demo_candidate_count=...
[gate21i] Pipeline complete
[gate21i] Actual corpus search-context summary completed
```

Exact counts depend on the generated search-context manifest.

## Runtime Artifacts

The runner writes or modifies generated local artifacts including:

```text
kbs/manifests/actual_corpus_source_inventory.json
kbs/manifests/kb_search_context_manifest.json
kbs/search_context/
kbs/retrieval/kb_actual_corpus_search_context_extraction.v1.json
kbs/retrieval/kb_actual_corpus_search_context_summary.v1.json
```

These generated artifacts should not be committed.

## Completion Criteria

Gate 21I is complete when:

1. Search-context summary reporter exists.
2. Validator covers missing and populated manifest states.
3. Runner validates and summarizes the actual corpus manifest.
4. Local validation passes.
5. PR diff contains only Gate 21I source and checkpoint files.
6. No generated `kbs/` artifacts are committed.

## Next Gate Candidate

Gate 21J — Actual Corpus Demo Query Candidate Capture or Customer Discovery Packet
