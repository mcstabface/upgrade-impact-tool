# Actual Corpus Customer Discovery Demo Packet

## Purpose

This packet prepares the customer conversation after the actual corpus successfully passed readiness, inventory, extraction, and summary gates.

The goal is to use a small evidence-backed demo to learn what the customer actually needs from the corpus before building additional retrieval behavior.

## Current Validated Corpus State

```text
actual_corpus_root=kbs/raw
actual_corpus_file_count=25
actual_corpus_total_size_bytes=42971911
html_source_count=4
portfolio_file_count=21
kb_document_count=4
matched_row_count=179
search_context_artifact_count=179
extraction_failed_count=0
empty_text_count=0
image_bearing_artifact_count=178
highlight_bearing_artifact_count=0
total_extracted_char_count=1479153
total_page_count=1353
demo_candidate_count=10
```

## Demo Objective

Show that the system can:

1. Ingest the actual corpus.
2. Extract searchable evidence from the corpus.
3. Preserve source lineage and artifact traceability.
4. Surface corpus-level extraction health.
5. Prepare customer questions before tuning retrieval behavior.

## Demo Narrative

### 1. Corpus present

The customer-provided corpus is available under:

```text
kbs/raw
```

The corpus contains 25 files, including 4 KB HTML sources and 21 portfolio PDFs.

### 2. Corpus structurally ready

The ingestion dry run found:

```text
missing_portfolio_count=0
unreferenced_portfolio_count=0
```

This means the detected HTML sources and portfolio PDFs line up structurally.

### 3. Search-context extraction successful

The extraction path produced:

```text
search_context_artifact_count=179
extraction_failed_count=0
empty_text_count=0
```

The corpus now has extractable evidence suitable for demo query preparation.

### 4. Caveat for visual artifacts

Most extracted artifacts are image-bearing:

```text
image_bearing_artifact_count=178
```

This means many source PDFs may contain visual content that should be reviewed if the customer expects image, table, or layout-sensitive answers.

## What The Demo Should Prove

The demo should prove controlled evidence extraction, not final answer quality.

Recommended wording:

```text
We have verified that your current corpus can be processed into traceable search-context artifacts. Before tuning retrieval or adding answer behavior, we want to validate the questions, evidence format, and decision workflows that matter to you.
```

## What Not To Promise

Do not claim:

- final retrieval quality is tuned
- customer question coverage is known
- image/table understanding is complete
- semantic retrieval is enabled
- hybrid retrieval is enabled for this runtime path
- the system knows the customer's priorities without customer input

## Customer Discovery Questions

### Business Use

```text
What decisions will this corpus support?
Who is the primary user: analyst, engineer, auditor, operator, or manager?
Is the desired workflow search, review, reporting, audit, or question answering?
What is the consequence of a missed relevant source?
What is the consequence of an irrelevant source appearing in the result set?
```

### Query Expectations

```text
What are the top 5-10 questions users need answered from this corpus?
Which terms, product names, fix identifiers, or release names must be searchable?
Do users search by KB ID, bug/patch number, product, category, symptom, or description?
Do users expect exact source excerpts or synthesized answers?
```

### Evidence Expectations

```text
What evidence must be shown with each answer?
Do users need PDF filename, KB document ID, bug/patch number, page number, or excerpt?
Is a source list enough, or must the answer quote supporting evidence?
Should image-bearing sources be flagged for manual review?
```

### Output Expectations

```text
What should the final output look like?
Should results be exported as markdown, JSON, CSV, PDF, or a UI view?
Should the system produce a short answer, an evidence table, or a structured report?
Are citations mandatory?
```

### Acceptance Criteria

```text
What would make the demo successful?
What would make the demo unacceptable?
Which examples should we use as known-good test cases?
Which examples should we treat as must-not-fail cases?
```

## Suggested Demo Flow

1. Show corpus summary metrics.
2. Show extraction health metrics.
3. Show sample search-context artifact lineage.
4. Show example extracted evidence from one candidate artifact.
5. Ask customer for their real questions.
6. Convert customer questions into a demo query candidate list.
7. Use those questions to define the next implementation gate.

## Recommended Customer Ask

```text
Please provide 5-10 representative questions you expect this corpus to answer, plus 2-3 examples of answers or evidence formats that would be useful to your team.
```

## Proposed Next Gate After Customer Input

Gate 21K — Customer Demo Query Set Capture

The next gate should record customer-provided questions, expected evidence shape, and acceptance criteria before tuning retrieval or adding answer behavior.

## Stop Condition

Do not add additional retrieval features until customer questions and acceptance criteria are captured.
