# Gate 21E Actual Corpus Source Inventory Extraction Build Plan

## Gate

Gate 21E — Actual Corpus Source Inventory Extraction

## Purpose

Gate 21E runs the existing KB source inventory extraction path against the actual customer corpus rooted at:

```text
kbs/raw
```

This gate produces the actual local source inventory manifest needed before search-context extraction and retrieval demo preparation.

## Why This Gate Exists

Gate 21C confirmed the corpus exists. Gate 21D confirmed the corpus is structurally ready for ingestion. Gate 21E performs the actual source inventory extraction using the existing manifest builder.

## Scope

The extraction reports:

- whether `kbs/raw` exists
- output inventory manifest path
- HTML source count
- PDF portfolio count
- KB document count
- missing referenced portfolio count
- unreferenced portfolio count
- extraction warnings and errors

## Non-Goals

Gate 21E does not:

- mutate corpus files
- extract search context
- chunk documents
- build embeddings
- build indexes
- run retrieval
- enable semantic vector retrieval
- enable hybrid retrieval
- commit generated `kbs/` reports or manifests

## Files Planned

```text
backend/app/scripts/actual_corpus_source_inventory_extraction.py
backend/app/scripts/validate_actual_corpus_source_inventory_extraction.py
backend/app/scripts/run_gate21e_actual_corpus_source_inventory_extraction.py
docs/checkpoints/Gate 21E Actual Corpus Source Inventory Extraction Build Plan.md
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate21e_actual_corpus_source_inventory_extraction
```

## Expected Validation Output

```text
[gate21e:source-inventory] OK
[gate21e:source-inventory] missing_root=failed
[gate21e:source-inventory] empty_root=failed_with_manifest
[gate21e:source-inventory] populated_root=extracted
[gate21e:source-inventory] Wrote inventory manifest: .../kbs/manifests/actual_corpus_source_inventory.json
[gate21e:source-inventory] Wrote extraction report: .../kbs/retrieval/kb_actual_corpus_source_inventory_extraction.v1.json
[gate21e:source-inventory] status=ACTUAL_CORPUS_SOURCE_INVENTORY_EXTRACTED
[gate21e:source-inventory] source_root=kbs/raw
[gate21e:source-inventory] source_root_exists=true
[gate21e] Pipeline complete
[gate21e] Actual corpus source inventory extraction completed for kbs/raw
```

The exact counts depend on the local corpus.

## Runtime Artifacts

The runner writes generated local artifacts:

```text
kbs/manifests/actual_corpus_source_inventory.json
kbs/retrieval/kb_actual_corpus_source_inventory_extraction.v1.json
```

These generated artifacts should not be committed.

## Completion Criteria

Gate 21E is complete when:

1. Source inventory extraction wrapper exists.
2. Validator covers missing, empty, and populated corpus roots.
3. Runner validates and extracts against `kbs/raw`.
4. Local validation passes.
5. PR diff contains only Gate 21E source and checkpoint files.
6. No generated `kbs/` artifacts are committed.

## Next Gate Candidate

Gate 21F — Actual Corpus Search Context Extraction Dry Run or Demo Query Candidate Capture
