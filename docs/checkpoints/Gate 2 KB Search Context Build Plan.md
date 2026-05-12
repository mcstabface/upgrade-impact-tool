# Gate 2 KB Search Context Build Plan

System: Upgrade Impact Analysis Tool  
Phase: KB Source Text Extraction and Search Context  
Status: Text extraction validated; deterministic chunking added for next run  
Generated: 2026-05-12

## Gate 1 Baseline

Gate 1 is complete for the current sample corpus. The verified pipeline produces:

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

The next gate must not reinterpret those results. It consumes `kbs/manifests/kb_evidence_map.json` as the source-of-truth join artifact from Gate 1.

## Gate 2 Objective

Gate 2 answers this bounded question:

> Can the system convert matched PFDS child PDFs into normalized, lineage-rich search-context artifacts suitable for chunking, retrieval, and later embedding?

This gate deliberately does **not** generate impact analysis. It only materializes retrieval-ready source context.

## Current Implementation

Gate 2 now has two deterministic stages.

| Stage | Script | Purpose |
|---|---|---|
| 2A | `backend/app/scripts/extract_kb_search_context.py` | Reads matched rows from `kb_evidence_map.json`, extracts child-PDF text with `pypdf`, preserves KB/PFDS lineage, detects image/highlight flags, writes normalized JSON artifacts. |
| 2B | `backend/app/scripts/chunk_kb_search_context.py` | Reads `kb_search_context_manifest.json`, chunks extracted PFDS text into deterministic fixed-character retrieval units, writes chunk collection artifacts and a chunk manifest. |
| Runner | `backend/app/scripts/run_gate2_kb_search_context.py` | Runs both Gate 2 stages and verifies expected manifest outputs. |

## Generated Outputs

| Artifact | Purpose |
|---|---|
| `kbs/search_context/<KB>/*.json` | One search-context artifact per matched PFDS evidence attachment. |
| `kbs/manifests/kb_search_context_manifest.json` | Gate 2 text extraction manifest with artifact paths, extraction counts, image/highlight counts, failures, and warnings. |
| `kbs/search_context_chunks/<KB>/*__chunks.json` | One chunk collection artifact per source search-context artifact with non-empty text. |
| `kbs/manifests/kb_search_context_chunks_manifest.json` | Gate 2 chunking manifest with collection paths, chunk counts, lineage, skipped records, failures, and warnings. |

## Verified Gate 2A Result

Local run reported by operator:

```text
python -m app.scripts.run_gate2_kb_search_context  27.97s user 0.05s system 99% cpu 28.121 total
```

Committed manifest shows:

```text
artifact_count = 179
```

This matches the Gate 1 matched PFDS evidence row count for the current corpus.

The manifest also shows that PFDS files are frequently image-bearing, which is expected for PDF design documents and must remain visible for review.

## Run Commands

From backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate2_kb_search_context
```

Dry run:

```bash
python -m app.scripts.run_gate2_kb_search_context --dry-run
```

Direct text extraction invocation:

```bash
python -m app.scripts.extract_kb_search_context \
  --evidence-map ../kbs/manifests/kb_evidence_map.json \
  --output-root ../kbs/search_context \
  --manifest-output ../kbs/manifests/kb_search_context_manifest.json
```

Direct chunking invocation:

```bash
python -m app.scripts.chunk_kb_search_context \
  --source-manifest ../kbs/manifests/kb_search_context_manifest.json \
  --output-root ../kbs/search_context_chunks \
  --manifest-output ../kbs/manifests/kb_search_context_chunks_manifest.json \
  --target-chars 2000 \
  --overlap-chars 200
```

## Search-Context Artifact Schema

Each search-context artifact uses:

```json
{
  "artifact_type": "kb_source_search_context",
  "schema_version": "kb_source_search_context.v1",
  "generated_utc": "...",
  "source_lineage": {
    "kb_document_id": "KB881136",
    "source_html": "kbs/raw/...html",
    "maintenance_pack": "MP 1",
    "hot_fix_release_label": "April 04, 2026",
    "portfolio_file": "..._PFDs_Portfolio.pdf",
    "child_pdf_path": "kbs/extracted/...pdf",
    "child_sha256": "..."
  },
  "kb_row": {
    "bug_patch_number": "...",
    "product": "...",
    "category": "...",
    "description": "...",
    "mapping_status": "MATCHED"
  },
  "evidence_attachment": {},
  "extraction": {
    "extractor": "pypdf",
    "extractor_version": "v1",
    "status": "SUCCESS",
    "page_count": 0,
    "char_count": 0,
    "text_sha256": "..."
  },
  "context_flags": {
    "has_text": true,
    "has_images": false,
    "image_count": 0,
    "has_highlight_annotations": false,
    "highlight_annotation_count": 0
  },
  "content": {
    "text": "...",
    "char_count": 0
  },
  "pages": []
}
```

## Chunk Collection Artifact Schema

Each chunk collection artifact uses:

```json
{
  "artifact_type": "kb_source_search_context_chunk_collection",
  "schema_version": "kb_source_search_context_chunk_collection.v1",
  "generated_utc": "...",
  "source_artifact_path": "kbs/search_context/KB...json",
  "source_lineage": {},
  "kb_row": {},
  "chunking": {
    "strategy": "fixed_chars_with_overlap",
    "target_chars": 2000,
    "overlap_chars": 200,
    "source_char_count": 0,
    "chunk_count": 0
  },
  "chunks": [
    {
      "chunk_id": "KB881136::39048140::<child_sha256>::0000",
      "chunk_index": 0,
      "chunk_count": 1,
      "content": {
        "text": "...",
        "char_count": 0,
        "token_estimate": 0,
        "text_sha256": "..."
      },
      "position": {
        "start_char": 0,
        "end_char": 0
      },
      "lineage": {
        "kb_document_id": "KB881136",
        "bug_patch_number": "39048140",
        "child_sha256": "...",
        "source_artifact_path": "kbs/search_context/...json"
      }
    }
  ]
}
```

## Acceptance Criteria

Gate 2 text extraction is complete when:

1. `python -m app.scripts.run_gate2_kb_search_context` completes successfully.
2. `kbs/manifests/kb_search_context_manifest.json` exists.
3. Manifest `matched_row_count` equals the Gate 1 matched PFDS evidence row count for the same corpus.
4. Manifest `artifact_count + extraction_failed_count` equals `matched_row_count`.
5. Every successful artifact preserves these lineage fields:
   - `kb_document_id`
   - `maintenance_pack`
   - `hot_fix_release_label`
   - `portfolio_file`
   - `child_pdf_path`
   - `child_sha256`
   - `bug_patch_number`
   - `product`
   - `category`
   - `description`
6. Image-bearing and highlight-bearing PDFs are flagged in the manifest for reviewer follow-up.

Gate 2 chunking is complete when:

1. `kbs/manifests/kb_search_context_chunks_manifest.json` exists.
2. Manifest `source_artifact_count` equals the text extraction manifest `artifact_count`.
3. Manifest `chunk_collection_count + skipped_empty_text_count + failure_count` equals `source_artifact_count`.
4. Every chunk has a deterministic chunk ID:

```text
{kb_document_id}::{bug_patch_number}::{child_sha256}::{zero_padded_chunk_index}
```

5. Every chunk preserves source artifact lineage.

## Next Build Steps

### Step 1 — Run and inspect full Gate 2

Run the Gate 2 runner locally and inspect both manifests:

```bash
python -m app.scripts.run_gate2_kb_search_context
python - <<'PY'
import json
from pathlib import Path
text = json.loads(Path('../kbs/manifests/kb_search_context_manifest.json').read_text())
chunks = json.loads(Path('../kbs/manifests/kb_search_context_chunks_manifest.json').read_text())
print('TEXT')
print(json.dumps({k: text[k] for k in [
  'matched_row_count',
  'artifact_count',
  'extraction_failed_count',
  'empty_text_count',
  'image_bearing_artifact_count',
  'highlight_bearing_artifact_count',
]}, indent=2))
print('CHUNKS')
print(json.dumps({k: chunks[k] for k in [
  'source_artifact_count',
  'chunk_collection_count',
  'chunk_count',
  'skipped_empty_text_count',
  'failure_count',
]}, indent=2))
PY
```

### Step 2 — Add manifest validation helper

Add a script that checks both Gate 2 manifest invariants and exits non-zero on mismatch.

Candidate file:

```text
backend/app/scripts/validate_gate2_kb_search_context.py
```

### Step 3 — UI bridge

Expose the Gate 2 manifest in the web UI as a reviewer-facing source corpus view:

- KB document
- maintenance pack
- bug / patch
- product
- category
- child PDF
- text availability
- image/highlight flags
- chunk count

## Non-Goals for This Gate

Gate 2 does not:

- generate upgrade impact analysis,
- infer functional impact,
- summarize PFDS content as truth,
- embed chunks,
- call an LLM,
- resolve missing Gate 1 evidence exceptions.

Those are later gates.

## Notes

`kbs/extracted/`, `kbs/search_context/`, and `kbs/search_context_chunks/` are generated artifacts and are ignored by Git. Manifests remain reviewable and may be committed intentionally.
