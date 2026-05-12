# Gate 2 KB Search Context Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: KB Source Text Extraction and Search Context  
Status: Complete for current sample corpus  
Generated: 2026-05-12

## Purpose

This checkpoint captures the completed state of Gate 2 for the KB ingestion/customization phase.

Gate 2 answered this bounded question:

> Can the system convert Gate 1 matched PFDS evidence into normalized, lineage-rich search-context artifacts and deterministic retrieval chunks?

For the current sample corpus, the answer is yes.

The pipeline is now repeatable through one orchestrator script and produces text extraction artifacts, chunk collection artifacts, validation checks, and a reviewer-facing Markdown summary.

## Source Corpus Baseline

Gate 2 starts from Gate 1 evidence mapping.

Current Gate 1 baseline:

- 4 KB HTML source pages
- 21 PDF Portfolio files
- 180 extracted child attachments
- 202 KB fix rows
- 179 matched PFDS evidence rows
- 1 portfolio no-PFDS placeholder row
- 6 KB-declared no-PFD rows
- 10 missing PFDS evidence rows
- 6 non-joinable rows
- 0 duplicate evidence rows

Gate 2 processes only matched PFDS evidence rows.

It does not reinterpret missing evidence, no-PFD placeholders, or non-joinable KB rows.

## Gate 2 Pipeline

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate2_kb_search_context
```

Dry run:

```bash
python -m app.scripts.run_gate2_kb_search_context --dry-run
```

The orchestrator runs these modules in order:

1. `app.scripts.extract_kb_search_context`
2. `app.scripts.chunk_kb_search_context`
3. `app.scripts.validate_gate2_kb_search_context`
4. `app.scripts.write_kb_search_context_summary`

## Generated Artifacts

| Artifact | Purpose |
|---|---|
| `kbs/search_context/<KB>/*.json` | One normalized search-context artifact per matched PFDS evidence attachment |
| `kbs/manifests/kb_search_context_manifest.json` | Text extraction manifest with lineage, extraction counts, image/highlight flags, failures, and warnings |
| `kbs/search_context_chunks/<KB>/*__chunks.json` | Deterministic fixed-character chunk collections for each non-empty search-context artifact |
| `kbs/manifests/kb_search_context_chunks_manifest.json` | Chunking manifest with collection paths, chunk counts, lineage, skipped records, failures, and warnings |
| `kbs/manifests/kb_search_context_summary.md` | Reviewer-facing Gate 2 summary report |

Generated text and chunk artifacts are ignored by Git:

- `kbs/search_context/`
- `kbs/search_context_chunks/`

Manifests remain reviewable and may be committed intentionally.

## Latest Verified Pipeline Output

Text extraction:

- Matched PFDS evidence rows: 179
- Search-context artifacts: 179
- Text extraction failures: 0
- Empty-text artifacts: 0
- Image-bearing artifacts: 178
- Highlight-bearing artifacts: 0

Chunking:

- Chunk collections: 179
- Chunks: 895
- Chunking skipped empty-text artifacts: 0
- Chunking failures: 0

Validation:

- Text invariant satisfied:

```text
artifact_count + extraction_failed_count == matched_row_count
179 + 0 == 179
```

- Chunk invariant satisfied:

```text
chunk_collection_count + skipped_empty_text_count + failure_count == source_artifact_count
179 + 0 + 0 == 179
```

## Per-KB Output Counts

| KB | Text Artifacts | Chunk Collections | Chunks | Image-Bearing | Highlights | Empty Text |
|---|---:|---:|---:|---:|---:|---:|
| KB869018 | 34 | 34 | 164 | 34 | 0 | 0 |
| KB875759 | 56 | 56 | 306 | 56 | 0 | 0 |
| KB881135 | 35 | 35 | 179 | 34 | 0 | 0 |
| KB881136 | 54 | 54 | 246 | 54 | 0 | 0 |

## Product Breakdown

| Product | Search-Context Artifacts |
|---|---:|
| Oracle Utilities Framework | 55 |
| Oracle Utilities Customer Care and Billing | 53 |
| Oracle Utilities Service and Measurement Data Foundation | 47 |
| Oracle Utilities Customer to Meter | 18 |
| Oracle Utilities Cloud Service Foundation | 4 |
| Oracle Utilities Asset Management Base | 2 |

## Key Code Added During Gate 2

| Script | Purpose |
|---|---|
| `backend/app/scripts/extract_kb_search_context.py` | Extract normalized text from matched PFDS child PDFs and write lineage-rich search-context artifacts |
| `backend/app/scripts/chunk_kb_search_context.py` | Chunk search-context text into deterministic fixed-character retrieval units |
| `backend/app/scripts/validate_gate2_kb_search_context.py` | Validate Gate 2 text and chunk manifest invariants |
| `backend/app/scripts/write_kb_search_context_summary.py` | Produce reviewer-facing Markdown summary from Gate 2 manifests |
| `backend/app/scripts/run_gate2_kb_search_context.py` | Run the full Gate 2 pipeline end-to-end |

## Search-Context Artifact Contract

Each source artifact uses:

```text
artifact_type = kb_source_search_context
schema_version = kb_source_search_context.v1
```

It preserves:

- KB document ID
- source HTML
- maintenance pack
- hot fix release label
- portfolio file
- child PDF path
- child SHA-256
- bug / patch number
- product
- category
- description
- mapping status
- extraction metadata
- text hash
- page-level text
- image flags
- highlight annotation flags

## Chunk Artifact Contract

Each chunk collection uses:

```text
artifact_type = kb_source_search_context_chunk_collection
schema_version = kb_source_search_context_chunk_collection.v1
```

Chunking strategy:

```text
fixed_chars_with_overlap
target_chars = 2000
overlap_chars = 200
```

Chunk ID format:

```text
{kb_document_id}::{bug_patch_number}::{child_sha256}::{zero_padded_chunk_index}
```

Example:

```text
KB881136::39048140::5337e1dffa8ebfde5bb747ad891a357a44102bd244b14f57ad33b45d390eb31e::0000
```

## What This Proves

Gate 2 proves that the project can now:

- consume Gate 1 evidence mapping as source truth,
- extract text from matched PFDS child PDFs,
- preserve KB and PDF lineage into normalized JSON artifacts,
- detect image-bearing PDF artifacts for reviewer awareness,
- detect PDF highlight annotations where present,
- produce deterministic chunk collections,
- preserve source lineage on every chunk,
- validate text and chunk manifest invariants,
- produce a reviewer-facing Markdown summary.

## Important Finding

178 of 179 matched PFDS artifacts are image-bearing.

This means text extraction is sufficient to create a retrieval substrate, but it may not capture every visually represented design element. Later gates should continue to surface image-heavy PFDS files during search/review and should not present text-only retrieval as complete visual understanding.

## Known Limitations

Gate 2 remains deliberately file-based and manifest-based.

Known limitations:

- It does not embed chunks.
- It does not build a lexical or vector search index.
- It does not provide a search API yet.
- It does not expose Gate 2 artifacts in the web UI yet.
- It does not run OCR or image understanding on image-heavy PFDS pages.
- It does not generate upgrade impact analysis.
- It does not resolve Gate 1 missing-evidence or non-joinable rows.
- It assumes Gate 1 generated `kbs/extracted/` artifacts are available locally.

These limitations are acceptable for Gate 2. They define the next gate.

## Recommended Next Gate

Recommended next gate:

**Gate 3 — KB PFDS Retrieval Index and Query**

Gate 3 should make the Gate 2 chunk artifacts searchable before any impact-analysis generation begins.

Proposed Gate 3 sequence:

1. Build a deterministic lexical index over `kbs/search_context_chunks/`.
2. Implement a simple KB PFDS query script over indexed chunks.
3. Return ranked chunks with KB/PFDS lineage:
   - KB document
   - maintenance pack
   - bug / patch number
   - product
   - category
   - source child PDF
   - chunk ID
4. Produce query-context artifacts under `kbs/query_context/`.
5. Add reviewer-facing query diagnostics.
6. Only after retrieval works, consider embedding or hybrid retrieval.

Do not start with impact generation. The next step is searchable evidence retrieval.

## Recommended Next Chat Starting Point

Use this prompt to continue in a new chat:

```text
We are continuing work on the Upgrade Impact Analysis Tool.

Gate 1 completed KB source extraction and PFDS evidence mapping.
Gate 2 completed KB PFDS source text extraction and deterministic chunking.

Use this repo as source of truth:
mcstabface/upgrade-impact-tool

Start from these docs/artifacts:
- docs/checkpoints/Gate 1 KB Source Extraction Completion Artifact.md
- docs/checkpoints/Gate 2 KB Search Context Completion Artifact.md
- kbs/manifests/kb_search_context_summary.md
- kbs/manifests/kb_search_context_manifest.json
- kbs/manifests/kb_search_context_chunks_manifest.json
- backend/app/scripts/run_gate2_kb_search_context.py

Current Gate 2 status:
- 179 matched PFDS evidence rows
- 179 search-context artifacts
- 0 text extraction failures
- 0 empty-text artifacts
- 178 image-bearing artifacts
- 0 highlight-bearing artifacts
- 179 chunk collections
- 895 chunks
- 0 chunking skips
- 0 chunking failures

The Gate 2 pipeline runs successfully with:
python -m app.scripts.run_gate2_kb_search_context

Next recommended gate is Gate 3: KB PFDS Retrieval Index and Query.

Please review the repo and produce the next concrete build plan and first patches for Gate 3.
Be specific, repo-grounded, and provide exact patch contents.
```

## Completion Status

Gate 2 is complete for the current source corpus.

The next work should begin from this checkpoint, not from memory.
