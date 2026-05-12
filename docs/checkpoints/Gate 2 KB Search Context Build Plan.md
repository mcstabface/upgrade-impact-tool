# Gate 2 KB Search Context Build Plan

System: Upgrade Impact Analysis Tool  
Phase: KB Source Text Extraction and Search Context  
Status: Initial build plan + first implementation slice  
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

## First Implementation Slice

The first slice adds a KB-specific bridge from Gate 1 evidence rows to search-context JSON artifacts.

Added scripts:

| Script | Purpose |
|---|---|
| `backend/app/scripts/extract_kb_search_context.py` | Reads matched rows from `kb_evidence_map.json`, extracts child-PDF text with `pypdf`, preserves KB/PFDS lineage, detects image/highlight flags, writes normalized JSON artifacts. |
| `backend/app/scripts/run_gate2_kb_search_context.py` | Runs the Gate 2 pipeline and verifies expected outputs. |

Generated outputs:

| Artifact | Purpose |
|---|---|
| `kbs/search_context/<KB>/*.json` | One search-context artifact per matched PFDS evidence attachment. |
| `kbs/manifests/kb_search_context_manifest.json` | Gate 2 manifest with artifact paths, extraction counts, image/highlight counts, failures, and warnings. |

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

Direct extractor invocation:

```bash
python -m app.scripts.extract_kb_search_context \
  --evidence-map ../kbs/manifests/kb_evidence_map.json \
  --output-root ../kbs/search_context \
  --manifest-output ../kbs/manifests/kb_search_context_manifest.json
```

## Artifact Schema

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

## Acceptance Criteria

Gate 2 initial slice is complete when:

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

## Next Build Steps

### Step 1 — Run and inspect Gate 2

Run the Gate 2 runner locally and inspect:

```bash
python -m app.scripts.run_gate2_kb_search_context
python - <<'PY'
import json
from pathlib import Path
m = json.loads(Path('../kbs/manifests/kb_search_context_manifest.json').read_text())
print(json.dumps({k: m[k] for k in [
  'matched_row_count',
  'artifact_count',
  'extraction_failed_count',
  'empty_text_count',
  'image_bearing_artifact_count',
  'highlight_bearing_artifact_count',
]}, indent=2))
PY
```

### Step 2 — Add chunk artifacts

Add a second Gate 2 stage that reads `kb_search_context_manifest.json` and writes deterministic chunks under:

```text
kbs/search_context_chunks/
```

Proposed chunk ID:

```text
{kb_document_id}::{bug_patch_number}::{child_sha256}::{zero_padded_chunk_index}
```

### Step 3 — Add retrieval manifest

Add `kbs/manifests/kb_search_context_chunks_manifest.json` with:

- source artifact path
- chunk count
- total characters
- text hash
- chunk IDs
- lineage fields repeated from the source context artifact

### Step 4 — UI bridge

Expose the Gate 2 manifest in the web UI as a reviewer-facing source corpus view:

- KB document
- maintenance pack
- bug / patch
- product
- category
- child PDF
- text availability
- image/highlight flags

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

`kbs/extracted/` is generated from portfolio PDFs and remains ignored by Git. `kbs/search_context/` should be treated the same way if artifacts become large; only manifests and source code should be committed unless small sample artifacts are intentionally added for tests.
