# Customer Demo Query Set Capture Worksheet

## Purpose

This worksheet captures customer-provided demo questions, expected evidence shape, and acceptance criteria for the actual corpus.

The worksheet should be filled from customer input. Do not invent queries or expected answers without customer confirmation.

## Source Context

This worksheet follows the actual corpus processing gates:

```text
Gate 21C — Actual Corpus Demo Readiness
Gate 21D — Actual Corpus Ingestion Dry Run
Gate 21E — Actual Corpus Source Inventory Extraction
Gate 21F — Actual Corpus Search Context Dry Run
Gate 21G — Actual Corpus Prerequisite Regeneration
Gate 21H — Actual Corpus Search Context Extraction
Gate 21I — Actual Corpus Search Context Summary
Gate 21J — Customer Discovery Demo Packet
```

Validated corpus state:

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

## Capture Rules

Use this worksheet to capture what the customer actually says.

Do not:

- fabricate customer questions
- assume acceptance criteria
- tune retrieval before examples are captured
- add semantic retrieval or hybrid retrieval for this runtime path without a concrete requirement
- treat internal demo candidates as customer priorities

## Customer Query Set

Capture 5-10 representative questions.

| ID | Customer Question | User Role | Search Mode | Must-Have Evidence | Expected Output | Acceptance Notes |
|---|---|---|---|---|---|---|
| Q01 | TBD | TBD | TBD | TBD | TBD | TBD |
| Q02 | TBD | TBD | TBD | TBD | TBD | TBD |
| Q03 | TBD | TBD | TBD | TBD | TBD | TBD |
| Q04 | TBD | TBD | TBD | TBD | TBD | TBD |
| Q05 | TBD | TBD | TBD | TBD | TBD | TBD |
| Q06 | TBD | TBD | TBD | TBD | TBD | TBD |
| Q07 | TBD | TBD | TBD | TBD | TBD | TBD |
| Q08 | TBD | TBD | TBD | TBD | TBD | TBD |
| Q09 | TBD | TBD | TBD | TBD | TBD | TBD |
| Q10 | TBD | TBD | TBD | TBD | TBD | TBD |

## Search Mode Options

Use one or more of the following labels:

```text
known_identifier
product_or_release
bug_or_patch_number
symptom_or_description
evidence_lookup
comparison
summary
exception_or_risk_review
```

## Evidence Requirements

For each question, capture which evidence fields matter:

```text
KB document ID
bug/patch number
product
category
description
portfolio filename
child PDF path
page number
excerpt
artifact path
image-bearing flag
```

## Output Shape Options

Possible desired outputs:

```text
short answer
ranked source list
evidence table
source excerpt list
markdown report
JSON export
CSV export
UI result card
```

## Acceptance Criteria Capture

For each query, capture:

```text
Top source must include:
Top 3 should include:
Must not include:
Evidence must show:
Failure condition:
Customer priority:
```

## Demo Readiness Questions

Ask the customer:

```text
Which 5-10 questions should we use for the first demo?
Which examples are must-not-fail?
What evidence would make you trust the result?
Do you need exact excerpts, source IDs, page references, or summaries?
Are image-heavy sources acceptable, or should they be flagged for manual review?
Who will use this: technical users, managers, auditors, or support staff?
```

## Post-Capture Output

After customer input is collected, this worksheet should feed the next gate:

```text
Gate 21L — Customer Demo Query Set Artifact
```

That gate should convert the captured questions into a structured query set artifact only after customer confirmation.

## Stop Condition

Do not build additional retrieval features until this worksheet is populated with customer-provided questions and acceptance criteria.
