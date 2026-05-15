# Gate 21K Customer Demo Query Set Capture Build Plan

## Gate

Gate 21K — Customer Demo Query Set Capture

## Purpose

Gate 21K creates a worksheet for capturing customer-provided demo questions, expected evidence shape, and acceptance criteria.

This is a documentation-only gate. It does not add runtime code, execute retrieval, or invent customer queries.

## Why This Gate Exists

Gate 21J created the customer discovery demo packet. The next required step is to collect the customer's real questions before additional retrieval behavior is built or tuned.

The project should not proceed into query tuning, answer synthesis, semantic retrieval, hybrid retrieval, or UI behavior until customer examples and acceptance criteria are captured.

## Inputs

Gate 21K uses validated actual-corpus metrics from prior gates:

```text
actual_corpus_file_count=25
html_source_count=4
portfolio_file_count=21
kb_document_count=4
search_context_artifact_count=179
extraction_failed_count=0
empty_text_count=0
total_extracted_char_count=1479153
total_page_count=1353
demo_candidate_count=10
```

## Scope

The worksheet captures:

- 5-10 representative customer questions
- user role
- search mode
- must-have evidence
- expected output shape
- acceptance notes
- evidence requirements
- failure conditions
- customer priorities

## Non-Goals

Gate 21K does not:

- invent demo queries
- infer customer priorities
- run retrieval
- tune ranking
- build a query artifact
- create a customer-facing UI
- enable semantic vector retrieval
- enable hybrid retrieval
- commit generated `kbs/` artifacts

## Files Planned

```text
docs/runbooks/Customer Demo Query Set Capture Worksheet.md
docs/checkpoints/Gate 21K Customer Demo Query Set Capture Build Plan.md
```

## Validation

No runtime validation is required because this gate is documentation-only.

Required verification:

```text
PR diff contains only documentation files.
No generated kbs/ artifacts are committed.
```

## Completion Criteria

Gate 21K is complete when:

1. Query capture worksheet exists.
2. Worksheet explicitly requires customer-provided questions.
3. Worksheet captures evidence expectations and acceptance criteria.
4. Worksheet includes a stop condition against speculative retrieval work.
5. Build plan exists.
6. PR diff contains only documentation files.

## Next Gate Candidate

Gate 21L — Customer Demo Query Set Artifact
