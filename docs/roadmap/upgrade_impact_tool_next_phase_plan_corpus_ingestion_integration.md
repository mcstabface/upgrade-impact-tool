# Upgrade Impact Tool — Next Phase Plan
## Corpus Ingestion Integration for KB-Driven Analysis

## Purpose

This phase adds a corpus-backed source layer to the Upgrade Impact Analysis Tool.

The goal is not to redesign the review product.
The goal is to replace manual KB-comparison legwork with a source-of-truth ingestion and retrieval path that prepares analyses for human review.

This phase assumes:
- KB articles remain the current source of truth,
- existing impacted-items and script workbooks are derived process artifacts,
- the current Upgrade Impact Tool UI and workflow remain valid as the review surface,
- the MK1 ingestion / retrieval pattern is the correct foundation for source ingestion.

---

## Problem Statement

The current tool supports a bounded, manual source-entry model.
That is sufficient for pilot workflow validation, but it does not match the actual source shape used in upgrade work.

The real process uses a corpus of KB articles and release material.
Humans currently read, compare, summarize, and convert that source corpus into working artifacts for review.

That means the missing capability is not more workflow UI.
The missing capability is a corpus-backed ingest layer that can:
- ingest the KB / release-note corpus,
- normalize it,
- retrieve relevant source material for a current-state → future-state transition,
- prepare candidate analysis content for review.

---

## Phase Objective

Attach a deterministic source-ingestion and retrieval layer to the Upgrade Impact Analysis Tool so the system can move from:

manual source entry
→ analysis prep
→ review

into:

KB corpus ingestion
→ retrieval against current/future state
→ analysis prep
→ review

---

## What This Phase Is

This phase is:
- corpus-backed analysis preparation,
- source-of-truth ingestion integration,
- API adaptation to support corpus-backed input,
- deterministic retrieval feeding the existing review workflow.

---

## What This Phase Is Not

This phase is not:
- a redesign of the current UI workflow,
- a replacement for human review,
- a new agentic planning system,
- a vague “AI search” feature,
- a rebuild of the app around embeddings.

The workflow product stays intact.
The source-prep layer gets stronger.

---

## Guiding Principles

### 1. Show process, not tech
The product story remains:
- ingest the source corpus,
- provide current state and future state,
- identify relevant source material,
- do the source-comparison legwork,
- prepare analysis for review.

Not:
- search context,
- chunking,
- embeddings,
- sharding,
- retrieval internals.

### 2. KB articles remain source of truth
Derived spreadsheets and manual summary workbooks may be useful as validation targets or schema hints, but they are not the authoritative input layer.

### 3. Existing review workflow remains the human decision layer
Keep:
- dashboard,
- analysis overview,
- review queue,
- review item detail,
- admin inspection.

### 4. Reuse proven ingestion pattern
The ingest path should follow the proven structure already built elsewhere:
- search context generation,
- chunking,
- embeddings,
- sharding / indexing where needed.

### 5. Backend-owned integration
Corpus registration, source typing, retrieval, and analysis preparation should remain backend-owned and auditable.

---

## Scope

## In Scope

### A. Source corpus model
Define a new backend concept for source-backed analysis.

Recommended term:
- `upgrade_source_corpus`

This should represent a curated source bundle for one release family, product line, or application scope.

### B. Corpus ingestion path
Add a new ingest path that can register and process source material used for upgrade analysis.

Initial corpus contents may include:
- KB articles,
- release notes,
- cumulative maintenance pack notes,
- attached supporting source documents.

### C. Retrieval-backed analysis preparation
Allow the analysis-prep layer to retrieve relevant source material from the corpus using:
- current state,
- future state,
- application/product context,
- optional module / release filters.

### D. API adaptation
Extend the existing API so an analysis can be prepared from:
- a manual source path, or
- a corpus-backed source path.

### E. Initial observability
Provide enough visibility to understand:
- which corpus was used,
- which sources were retrieved,
- which retrieved sources contributed to the prepared analysis.

---

## Out of Scope

### Not in this phase
- replacing the current review UI,
- polished bulk corpus admin UX,
- automated SharePoint-native sync,
- fully generalized spreadsheet/parser framework,
- semantic answer generation beyond analysis prep,
- major report redesign,
- corpus-wide contradiction modeling,
- full enterprise-scale retrieval hardening.

Those can come later.
This phase is meant to be small, direct, and useful.

---

## Proposed Architecture

## Current shape

Current system shape is effectively:
- manual intake context,
- current state / future state,
- bounded source references,
- analysis generation,
- review workflow.

## Next shape

Add a source layer in front of the analysis-prep path:

source corpus ingestion
→ normalized source artifacts
→ retrieval against state transition
→ prepared analysis candidate
→ existing review workflow

## Separation of concerns

### Ingestion / retrieval layer owns
- source registration,
- conversion / extraction,
- normalized search artifacts,
- chunking,
- embeddings,
- sharding / retrieval indexing,
- source retrieval.

### Upgrade Impact Tool owns
- intake and state inputs,
- analysis preparation rules,
- review queue and item workflow,
- audit / export,
- admin inspection.

That separation should remain clean.

---

## Core Data / Domain Additions

## 1. Upgrade source corpus
Add a first-class entity representing a source corpus.

Suggested fields:
- `corpus_id`
- `name`
- `source_type`
- `product_line`
- `release_family`
- `release_version`
- `status`
- `created_utc`
- `updated_utc`

## 2. Corpus source artifact
Represents a source document attached to a corpus.

Suggested fields:
- `source_artifact_id`
- `corpus_id`
- `logical_path`
- `artifact_type`
- `source_hash`
- `ingest_status`
- `created_utc`

## 3. Analysis source selection
When an analysis runs against a corpus, persist source selection metadata.

Suggested fields:
- `analysis_id`
- `corpus_id`
- `selected_source_ids`
- `selection_reason_summary`
- `retrieval_metadata`
- `created_utc`

This does not need to be over-designed in the first pass.
It just needs to be inspectable.

---

## Input Model Change

## Current model
The current model effectively assumes one or a few manually specified source references.

## Future model
Allow analysis prep to accept either:

### Mode 1 — manual source mode
Current bounded behavior.

### Mode 2 — corpus-backed mode
Input includes:
- current state,
- future state,
- application / product context,
- `corpus_id`,
- optional narrowing selectors.

Optional selectors may include:
- product line,
- app family,
- release,
- module,
- release train,
- source type.

This should be explicit and backend-owned.

---

## Retrieval Path

## Initial deterministic path
This phase does not need a new retrieval architecture.
It should reuse the existing proven pattern.

Recommended ingest / retrieval path:
1. source document extraction to search context
2. chunk generation
3. embeddings generation
4. sharding / indexing if needed
5. retrieval against state transition inputs

## Retrieval purpose in this product
Retrieval is not the final product.
Retrieval is the source-selection and evidence-prep layer for analysis generation.

That means the output of retrieval should be shaped toward:
- relevant KBs,
- relevant sections / chunks,
- supporting provenance,
- evidence ready to feed analysis prep.

---

## API Changes

## Goal
Extend the existing API rather than building a second system.

## Proposed additions

### 1. Corpus registration endpoints
Examples:
- create corpus
- attach source bundle
- trigger ingest / processing
- view corpus status

### 2. Analysis creation / preparation changes
Allow analysis creation to specify either:
- manual source inputs, or
- `corpus_id` + state transition context.

### 3. Source evidence inspection endpoint
Allow retrieval-backed source evidence used in an analysis to be viewed later.

This is useful for:
- admin inspection,
- debugging,
- analyst trust,
- future report support.

---

## UI Changes

## Rule
Do not redesign the current workflow.
Add only what is required to support corpus-backed input visibility.

## Minimum viable UI additions

### 1. Intake / analysis creation surface
Allow a user to choose:
- manual source entry, or
- corpus-backed source selection.

### 2. Analysis overview
Show:
- corpus used,
- source selection summary,
- key source evidence references.

### 3. Admin inspection
Add enough visibility to inspect:
- which corpus an analysis used,
- whether the source selection path was manual or corpus-backed,
- basic ingest / retrieval health.

No full corpus-management UI is required in this phase.

---

## Recommended Work Packages

## WP-01 — Corpus model and backend contract
Define:
- corpus entities,
- source artifact linkage,
- minimal ingest status model,
- analysis-to-corpus contract.

Deliverables:
- data model,
- API contract,
- migration / schema changes,
- initial status fields.

Exit criteria:
- backend can represent a corpus and attach source artifacts to it.

---

## WP-02 — Ingestion integration seam
Attach the standard ingest path behind the new corpus model.

Expected processing path:
- search context
- chunking
- embeddings
- sharding / indexing if needed

Deliverables:
- ingestion trigger,
- artifact path / registry linkage,
- ingest status updates,
- source artifact traceability.

Exit criteria:
- source artifacts attached to a corpus can be processed into retrieval-ready artifacts.

---

## WP-03 — Corpus-backed retrieval for analysis prep
Enable retrieval using:
- corpus scope,
- current state,
- future state,
- product/application context.

Deliverables:
- retrieval call path,
- selected-source output,
- retrieval metadata persisted with analysis prep.

Exit criteria:
- a corpus-backed analysis request returns inspectable source selections.

---

## WP-04 — Analysis prep adaptation
Use retrieved source evidence to prepare the initial analysis output for the existing workflow.

Deliverables:
- source-backed preparation path,
- provenance references,
- prepared candidate analysis content.

Exit criteria:
- retrieved source evidence can feed the existing analysis and review workflow.

---

## WP-05 — Minimal UI / inspection support
Expose enough visibility in the app to make corpus-backed behavior understandable.

Deliverables:
- corpus selection in the relevant input flow,
- analysis overview source summary,
- admin inspection source-path visibility.

Exit criteria:
- users can tell whether an analysis was manual or corpus-backed and what sources supported it.

---

## WP-06 — Validation against current manual process
Use the existing manually assembled workbooks as comparison targets, not source truth.

Deliverables:
- compare prepared analysis outputs to current manual outputs,
- identify missing fields / mismatches,
- refine extraction / prep rules.

Exit criteria:
- the system output is directionally aligned with what the current manual process is trying to produce.

---

## Execution Order

1. WP-01 — Corpus model and backend contract
2. WP-02 — Ingestion integration seam
3. WP-03 — Corpus-backed retrieval for analysis prep
4. WP-04 — Analysis prep adaptation
5. WP-05 — Minimal UI / inspection support
6. WP-06 — Validation against current manual process

That order keeps the work disciplined and avoids building UI before the data path exists.

---

## Minimum Viable Phase Outcome

This phase is successful if we can:
- register a KB/release-note corpus,
- process it through the standard ingest pattern,
- run an analysis using current state + future state + corpus scope,
- retrieve relevant source material,
- prepare an initial analysis for review,
- preserve traceability to the retrieved source evidence,
- surface that evidence path in the existing app.

That is enough to prove the direction.

---

## Risks

## 1. Overbuilding the corpus-management layer
Risk:
Trying to build a full admin platform before the source-prep path exists.

Mitigation:
Keep UI and management features thin in this phase.

## 2. Treating manual workbook outputs as source truth
Risk:
Building around downstream artifacts instead of KB source material.

Mitigation:
Use workbooks as validation targets only.

## 3. Overcomplicating analysis generation too early
Risk:
Trying to solve every inference problem before source selection and provenance are stable.

Mitigation:
Keep this phase focused on source-backed prep, not full autonomous reasoning.

## 4. Entangling ingestion and review layers
Risk:
Turning the review app into the ingest engine.

Mitigation:
Preserve separation of concerns.

---

## Recommended Deliverable Framing

This phase should be described internally as:

**Corpus-Backed Analysis Preparation**

Not:
- AI ingest,
- semantic upgrade engine,
- intelligent KB search,
- autonomous analysis.

The value is practical and process-aligned:
- reduce manual source-comparison work,
- prepare structured analysis input,
- hand off to human review.

---

## Suggested Talking Point

“If the KB articles are the source of truth, then the opportunity is to ingest that corpus directly, feed in current state and future state, let the system do the comparison work that is currently being done manually, and prepare the analysis for review.”

---

## Immediate Next Step

Write the technical design for WP-01 and WP-02 together:
- corpus entity contract,
- source artifact registration model,
- ingest trigger shape,
- API changes required to support corpus-backed analysis.

That should be the next concrete build artifact.

---

## Bottom Line

This is not a large architectural leap.
It is a controlled extension of the product in the right place.

We already have:
- the review workflow,
- the admin/inspection layer,
- the ingest pattern,
- the retrieval pattern.

The next phase is to connect them cleanly so the tool can move from manual source entry to corpus-backed analysis preparation.

