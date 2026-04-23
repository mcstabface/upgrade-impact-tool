# Upgrade Impact Tool — WP-01 / WP-02 Technical Design
## Corpus Model and Ingestion Integration Seam

## Purpose

This document defines the first implementation slice for corpus-backed analysis preparation.

It covers:
- WP-01 — corpus model and backend contract
- WP-02 — ingestion integration seam

The goal is to make corpus-backed analysis buildable without redesigning the current product.

This is the point where we move from roadmap language into an actual system contract.

---

## Design Intent

The Upgrade Impact Analysis Tool already has:
- authenticated workflow surfaces,
- analysis and review lifecycle,
- exports and admin inspection,
- pilot-ready bounded manual mode.

The missing layer is source-of-truth ingestion.

This design adds a backend-owned corpus model and a clean ingestion seam so the product can evolve from:

manual source entry
→ analysis prep
→ review

into:

source corpus registration
→ ingest / normalize / index
→ retrieve relevant source material
→ prepare analysis
→ review

---

## Non-Negotiable Constraints

### 1. KB articles remain source of truth
Derived spreadsheets are process outputs or validation targets, not primary truth.

### 2. Current review workflow remains intact
Do not redesign:
- dashboard
- analysis overview
- review queue
- review item detail
- admin inspection

### 3. Ingestion stays backend-owned
The frontend may initiate or display status, but ingestion state and source typing remain backend-owned.

### 4. Source processing must be auditable
The system must be able to answer:
- what corpus was used,
- what source artifacts were attached,
- what ingest state each artifact reached,
- what source evidence supported an analysis.

### 5. Integration should reuse the proven ingestion pattern
The ingestion seam should allow the standard path:
- search context
- chunking
- embeddings
- sharding / indexing if needed

without forcing the Upgrade Impact Tool to become the ingestion engine itself.

---

## Phase Outcome

WP-01 and WP-02 are complete when the backend can:
- represent a corpus,
- attach source artifacts to it,
- track artifact type and ingest status,
- trigger ingest processing for attached sources,
- persist enough metadata for later retrieval-backed analysis.

This phase does not yet require a finished corpus-management UI.

---

# Part 1 — Domain Model

## New Core Entity: UpgradeSourceCorpus

Represents a curated source corpus used for upgrade analysis.

A corpus may be scoped to:
- a product line,
- an application family,
- a release family,
- a specific release,
- or another bounded upgrade source set.

### Required fields
- `corpus_id: str`
- `name: str`
- `description: str | null`
- `product_line: str | null`
- `application_family: str | null`
- `release_family: str | null`
- `release_version: str | null`
- `status: str`
- `created_utc: int`
- `updated_utc: int`

### Recommended status enum
- `DRAFT`
- `READY`
- `INGESTING`
- `PARTIALLY_INGESTED`
- `INGESTED`
- `FAILED`
- `ARCHIVED`

### Status meaning
- `DRAFT` — corpus exists, sources may still be incomplete
- `READY` — source list is attached and ready to ingest
- `INGESTING` — processing in progress
- `PARTIALLY_INGESTED` — some sources processed, at least one failed or pending
- `INGESTED` — all required sources processed successfully
- `FAILED` — corpus-level ingest failed materially
- `ARCHIVED` — no longer active for new analysis runs

---

## New Core Entity: CorpusSourceArtifact

Represents one source artifact attached to a corpus.

This is the key seam between the Upgrade Impact Tool and the ingest layer.

### Required fields
- `source_artifact_id: str`
- `corpus_id: str`
- `logical_name: str`
- `logical_path: str`
- `source_type: str`
- `source_hash: str | null`
- `storage_path: str`
- `content_type: str | null`
- `ingest_status: str`
- `ingest_error_code: str | null`
- `ingest_error_detail: str | null`
- `created_utc: int`
- `updated_utc: int`

### Recommended source_type enum (initial)
- `KB_ARTICLE`
- `RELEASE_NOTE`
- `CUMULATIVE_MP_NOTE`
- `SUPPORTING_DOC`
- `NESTED_CONTAINER`
- `UNKNOWN`

This enum should stay intentionally small in the first slice.
Do not over-model yet.

### Recommended ingest_status enum
- `REGISTERED`
- `QUEUED`
- `PROCESSING`
- `PROCESSED`
- `FAILED`
- `SKIPPED`

### Status meaning
- `REGISTERED` — artifact exists in corpus but processing not requested
- `QUEUED` — ready for ingest
- `PROCESSING` — ingest running now
- `PROCESSED` — ingest completed successfully
- `FAILED` — ingest failed
- `SKIPPED` — explicitly skipped by ingest policy or unsupported

---

## New Supporting Entity: CorpusIngestRun

Tracks a corpus-level ingest request and result.

This is not the full ingest engine audit model. It is the Upgrade Impact Tool’s local contract for corpus processing.

### Required fields
- `ingest_run_id: str`
- `corpus_id: str`
- `status: str`
- `requested_utc: int`
- `started_utc: int | null`
- `completed_utc: int | null`
- `requested_by_user_id: str | null`
- `artifact_count: int`
- `processed_count: int`
- `failed_count: int`
- `skipped_count: int`
- `note: str | null`

### Recommended status enum
- `QUEUED`
- `RUNNING`
- `COMPLETE`
- `FAILED`

---

## Future-facing entity (not required to implement in WP-01 / WP-02)

### AnalysisSourceSelection
This belongs to the next slice, but the corpus model should leave room for it.

It will eventually track:
- which source artifacts were retrieved,
- why they were selected,
- what retrieval metadata supported them,
- how they were attached to a prepared analysis.

---

# Part 2 — Database Design

## New table: `upgrade_source_corpora`

Suggested columns:

```sql
CREATE TABLE upgrade_source_corpora (
    corpus_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NULL,
    product_line TEXT NULL,
    application_family TEXT NULL,
    release_family TEXT NULL,
    release_version TEXT NULL,
    status TEXT NOT NULL,
    created_utc BIGINT NOT NULL,
    updated_utc BIGINT NOT NULL
);
```

### Recommended indexes
- index on `status`
- index on `(product_line, release_family, release_version)`

---

## New table: `corpus_source_artifacts`

Suggested columns:

```sql
CREATE TABLE corpus_source_artifacts (
    source_artifact_id TEXT PRIMARY KEY,
    corpus_id TEXT NOT NULL REFERENCES upgrade_source_corpora(corpus_id) ON DELETE CASCADE,
    logical_name TEXT NOT NULL,
    logical_path TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_hash TEXT NULL,
    storage_path TEXT NOT NULL,
    content_type TEXT NULL,
    ingest_status TEXT NOT NULL,
    ingest_error_code TEXT NULL,
    ingest_error_detail TEXT NULL,
    created_utc BIGINT NOT NULL,
    updated_utc BIGINT NOT NULL
);
```

### Recommended indexes
- index on `corpus_id`
- index on `(corpus_id, ingest_status)`
- index on `(corpus_id, source_type)`

### Optional uniqueness guard
If desired in first pass:
- unique on `(corpus_id, logical_path)`

That is enough to prevent obvious duplicates without overcomplicating versioning.

---

## New table: `corpus_ingest_runs`

Suggested columns:

```sql
CREATE TABLE corpus_ingest_runs (
    ingest_run_id TEXT PRIMARY KEY,
    corpus_id TEXT NOT NULL REFERENCES upgrade_source_corpora(corpus_id) ON DELETE CASCADE,
    status TEXT NOT NULL,
    requested_utc BIGINT NOT NULL,
    started_utc BIGINT NULL,
    completed_utc BIGINT NULL,
    requested_by_user_id TEXT NULL,
    artifact_count INTEGER NOT NULL,
    processed_count INTEGER NOT NULL,
    failed_count INTEGER NOT NULL,
    skipped_count INTEGER NOT NULL,
    note TEXT NULL
);
```

### Recommended index
- index on `corpus_id`

---

# Part 3 — Backend Contract

## API Design Goals

The API should:
- create and inspect corpora,
- attach sources,
- trigger ingest,
- report ingest status,
- stay compatible with the existing analysis workflow.

The API should not, in this phase:
- expose every ingest-engine internal,
- require a full admin UI to be useful,
- collapse manual and corpus-backed modes into one ambiguous payload.

---

## Endpoint Group 1 — Corpus lifecycle

### `POST /api/v1/corpora`
Create a new corpus.

#### Request body
```json
{
  "name": "CCS 25.10 KB Corpus",
  "description": "Primary KB and release-note corpus for CCS 25.10 analysis",
  "product_line": "CCS",
  "application_family": "UIMS",
  "release_family": "25.x",
  "release_version": "25.10"
}
```

#### Response
```json
{
  "corpus_id": "corpus_...",
  "status": "DRAFT"
}
```

---

### `GET /api/v1/corpora/{corpus_id}`
Return corpus metadata and counts.

#### Response should include
- corpus fields
- source counts by ingest status
- source counts by source type
- latest ingest run summary if present

---

### `GET /api/v1/corpora`
Return corpus list with lightweight summaries.

Useful for future UI and admin inspection.

---

## Endpoint Group 2 — Attach source artifacts

### `POST /api/v1/corpora/{corpus_id}/sources`
Attach one or more source artifacts to a corpus.

Initial implementation can assume storage paths already exist and are reachable by the backend.

#### Request body
```json
{
  "sources": [
    {
      "logical_name": "CCS_25.10_Cumulative_MPs.xlsx",
      "logical_path": "25.10/CCS_25.10_Cumulative_MPs.xlsx",
      "source_type": "CUMULATIVE_MP_NOTE",
      "storage_path": "/data/imports/25.10/CCS_25.10_Cumulative_MPs.xlsx",
      "content_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    }
  ]
}
```

#### Response
- created `source_artifact_id` values
- current `ingest_status` for each artifact

---

### `GET /api/v1/corpora/{corpus_id}/sources`
Return full source list for a corpus.

Useful fields:
- logical name
- source type
- ingest status
- error fields if failed

---

## Endpoint Group 3 — Trigger and inspect ingest

### `POST /api/v1/corpora/{corpus_id}/ingest`
Trigger ingest for all eligible source artifacts in the corpus.

#### Request body
```json
{
  "reprocess_processed": false
}
```

#### Behavior
- create `corpus_ingest_run`
- move eligible artifacts from `REGISTERED` to `QUEUED`
- begin backend ingest orchestration

#### Response
```json
{
  "ingest_run_id": "ingest_...",
  "status": "QUEUED"
}
```

---

### `GET /api/v1/corpora/{corpus_id}/ingest-runs`
Return corpus ingest history.

---

### `GET /api/v1/corpora/{corpus_id}/ingest-runs/{ingest_run_id}`
Return one ingest run with aggregate counts.

This is enough for initial admin visibility.

---

# Part 4 — Ingestion Integration Seam

## Goal

Define the cleanest possible seam between:
- Upgrade Impact Tool backend
- existing ingest / retrieval pattern

The seam should be narrow and auditable.

## Core principle

The Upgrade Impact Tool should not implement search context conversion, chunking, embeddings, or sharding directly.

It should:
- register what needs to be ingested,
- invoke the ingest flow,
- receive/process status,
- persist linkage back to its own corpus/source model.

---

## Recommended seam contract

For each `CorpusSourceArtifact`, the ingest layer should be able to produce:
- normalized source artifact output
- processing status
- stable source hash
- ingest metadata
- referenceable retrieval-ready artifact lineage

### Minimal required integration output
For each processed source artifact, the Upgrade Impact Tool should be able to persist or obtain:
- `source_artifact_id`
- `source_hash`
- `processing_status`
- `search_context_artifact_ref`
- optional `chunk_collection_ref`
- optional `embedding_collection_ref`

This does not need to expose every artifact detail immediately.
It just needs stable linkage.

---

## Implementation options

### Option A — In-process integration
The backend directly calls the ingest pipeline code path.

Pros:
- fastest path
- fewer moving parts
- simplest for early implementation

Cons:
- tighter coupling
- later extraction into separate service becomes a refactor

### Option B — Local service / job boundary
The backend triggers a local ingest service or job runner.

Pros:
- cleaner separation
- better long-term scaling

Cons:
- more moving parts now
- more setup overhead

## Recommendation
For this phase, prefer **Option A** if it keeps the work small and direct.

The architecture goal is not perfect distributed purity.
The goal is to attach ingestion cleanly and quickly.

---

## Processing flow

Recommended high-level flow:

1. corpus exists
2. source artifacts attached
3. ingest requested
4. eligible source artifacts transition:
   - `REGISTERED` → `QUEUED` → `PROCESSING`
5. ingest pipeline runs on each artifact
6. processed artifacts transition to:
   - `PROCESSED` on success
   - `FAILED` on failure
   - `SKIPPED` if unsupported or intentionally bypassed
7. corpus ingest run updates aggregate counts
8. corpus status updates based on aggregate result

---

## Corpus status derivation rules

Suggested logic:
- if all required artifacts are `PROCESSED` → corpus `INGESTED`
- if at least one `PROCESSING` or `QUEUED` → corpus `INGESTING`
- if at least one `FAILED` and at least one `PROCESSED` → corpus `PARTIALLY_INGESTED`
- if all attempted and all failed → corpus `FAILED`
- if sources attached but not triggered yet → corpus `READY`

These can be backend-derived rather than manually managed everywhere.

---

# Part 5 — Analysis Compatibility Contract

## Goal

WP-01 / WP-02 do not yet require retrieval-backed analysis generation, but they must leave a clean path for it.

That means the analysis layer should eventually be able to accept:

```json
{
  "analysis_mode": "CORPUS_BACKED",
  "corpus_id": "corpus_...",
  "current_state": {...},
  "future_state": {...},
  "selectors": {
    "product_line": "CCS",
    "application_family": "UIMS",
    "release_version": "25.10"
  }
}
```

This payload does not need to be wired fully in WP-01 / WP-02, but the corpus data model should be designed to support it without rework.

---

# Part 6 — Minimal UI Support

## Rule
UI changes in this slice should be minimal and optional.

Recommended first support:
- admin-visible corpus list or corpus status endpoint consumption later
- no large UI build required now

If any UI support is added in this phase, it should be limited to:
- showing corpus existence
- showing ingest status
- showing source counts

Do not build a full corpus management interface yet.

---

# Part 7 — Error Handling

## Failures to support explicitly

### Corpus creation failures
- invalid release metadata
- duplicate/invalid payload

### Source attachment failures
- bad storage path
- duplicate logical path in corpus
- unsupported source type if enforced

### Ingest failures
- file missing
- extraction/conversion failure
- pipeline exception
- artifact validation failure

---

## Error response guidance

Use the same style already present in the app:
- explicit message
- recovery guidance where practical
- retryable flag where practical

Example corpus ingest failure shape:

```json
{
  "message": "Corpus ingest failed for one or more source artifacts.",
  "recovery_guidance": "Inspect failed source artifacts, correct invalid paths or unsupported files, then retry ingest.",
  "retryable": true
}
```

---

# Part 8 — Recommended Build Order

## Step 1
Create DB schema for:
- `upgrade_source_corpora`
- `corpus_source_artifacts`
- `corpus_ingest_runs`

## Step 2
Add backend models / schemas / service layer for corpus CRUD.

## Step 3
Add source attachment endpoints.

## Step 4
Add ingest-run creation endpoint and service contract.

## Step 5
Implement in-process ingest seam to update source artifact statuses.

## Step 6
Add corpus summary endpoint response fields:
- source counts by status
- source counts by type
- latest ingest run

This is the minimum coherent backend slice.

---

# Part 9 — Acceptance Criteria

WP-01 / WP-02 are done when all of the following are true:

- a corpus can be created,
- source artifacts can be attached,
- ingest can be requested,
- ingest statuses transition cleanly,
- corpus aggregate status is derived correctly,
- source artifacts are linked to retrieval-ready processing outputs,
- corpus state can be inspected via API,
- the design leaves a clean path for corpus-backed analysis in the next slice.

---

# Part 10 — Exact Next Build Artifact

The next build artifact after this document should be:

## `Corpus Model and Ingestion API Build Plan`

That build plan should list:
- exact backend files to add / modify
- migrations to write
- endpoint definitions to implement first
- status derivation logic
- ingest seam function contract

That will be the first code-facing implementation plan.

---

# Bottom Line

This is not a large conceptual leap.
It is a controlled backend extension that introduces:
- corpus identity,
- source artifact registration,
- ingest status tracking,
- a seam to the ingest/retrieval pipeline.

Once those exist, the next slice can focus on corpus-backed retrieval and analysis preparation without inventing the foundation midstream.

