# Gate 1 KB Source Extraction Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: KB Source Package Extraction and Evidence Mapping  
Status: Complete for current sample corpus  
Generated: 2026-05-12

## Purpose

This checkpoint captures the current state of Gate 1 for the KB ingestion/customization phase.

Gate 1 answered this bounded question:

> Can the system take real KB release source material, extract PDF Portfolio child documents, preserve source lineage, map KB table rows to extracted PFDS evidence, and produce reviewer-facing discrepancy artifacts?

For the current sample corpus, the answer is yes.

The pipeline is now repeatable through one orchestrator script and produces source inventory, extraction, evidence mapping, exception, CSV, and Markdown summary artifacts.

## Source Corpus

Current source inputs live under `kbs/`.

The current corpus contains:

- 4 downloaded KB HTML source pages
- 21 PDF Portfolio files
- 180 extracted child attachments
- 202 KB fix rows

Current KB documents:

| KB | Maintenance Pack | Source HTML |
|---|---|---|
| KB881136 | MP 1 | `kbs/raw/April 2026 Maintenance Pack - MP 1.html` |
| KB881135 | MP 7 | `kbs/raw/April 2026 Maintenance Pack - MP 7.html` |
| KB869018 | MP 5 | `kbs/raw/February 2026 Maintenance Pack - MP 5 - Starting after MP 5.3.1.html` |
| KB875759 | MP 6 | `kbs/raw/March 2026 Maintenance Pack - MP 6.html` |

## Gate 1 Pipeline

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate1_kb_extraction
```

Dry run:

```bash
python -m app.scripts.run_gate1_kb_extraction --dry-run
```

The orchestrator runs these modules in order:

1. `app.scripts.extract_kb_source_manifest`
2. `app.scripts.extract_pdf_portfolios`
3. `app.scripts.extract_kb_fix_rows`
4. `app.scripts.build_kb_evidence_map`
5. `app.scripts.summarize_kb_evidence_exceptions`
6. `app.scripts.export_kb_evidence_exceptions_csv`
7. `app.scripts.write_kb_evidence_summary`

## Generated Artifacts

| Artifact | Purpose |
|---|---|
| `kbs/manifests/source_inventory.json` | Source inventory of KB HTML pages and referenced portfolio PDFs |
| `kbs/manifests/portfolio_extraction.json` | Portfolio extraction manifest, child attachment metadata, hashes, candidate fix IDs |
| `kbs/manifests/kb_fix_rows.json` | Structured KB table rows with bug / patch, product, category, description, release section, and portfolio reference |
| `kbs/manifests/kb_evidence_map.json` | Join result mapping KB rows to extracted PFDS attachments |
| `kbs/manifests/kb_evidence_exceptions.json` | Reviewer-facing structured exception summary |
| `kbs/manifests/kb_evidence_exceptions.csv` | Spreadsheet-friendly exception export |
| `kbs/manifests/kb_evidence_exception_summary.md` | Meeting/readout summary report |

Generated extracted PDF children are written under `kbs/extracted/`.

`kbs/extracted/` is ignored by Git because those files are generated from source portfolio PDFs.

## Latest Verified Pipeline Output

Source inventory:

- KB HTML sources: 4
- Portfolio files: 21
- Missing referenced portfolios: 0
- Unreferenced portfolio files: 0

Portfolio extraction:

- Portfolio files processed: 21
- Extracted attachments: 180
- Candidate fix identifiers: 179
- Placeholder attachments: 1
- Unmapped attachments: 0
- Failed portfolios: 0

KB fix-row extraction:

- KB HTML sources: 4
- Fix rows extracted: 202
- Document warnings: 0
- Row warnings: 27

Evidence mapping:

- Documents: 4
- Fix rows: 202
- Matched rows: 179
- Placeholder rows: 1
- KB-declared no-PFD rows: 6
- Missing evidence rows: 10
- Non-joinable rows: 6
- Duplicate evidence rows: 0

Exception summary:

- Documents with exceptions: 4
- Exceptions: 23
- Severity counts:
  - HIGH: 10
  - MEDIUM: 6
  - LOW: 7
- Status counts:
  - KB_DECLARED_NO_PFD: 6
  - NO_EVIDENCE_ATTACHMENT_FOUND: 10
  - PORTFOLIO_PLACEHOLDER_NO_PFDS: 1
  - ROW_MISSING_FIX_IDENTIFIER: 6

CSV export:

- Rows exported: 23

Markdown summary:

- Exceptions summarized: 23

## Classification Model

| Status | Meaning | Severity |
|---|---|---|
| `MATCHED` | KB row matched exactly one extracted PFDS attachment by portfolio and bug / patch number | None |
| `NO_EVIDENCE_ATTACHMENT_FOUND` | KB row has a bug / patch number, but no extracted PFDS attachment matched within the referenced portfolio | HIGH |
| `ROW_MISSING_FIX_IDENTIFIER` | KB row has no bug / patch identifier, so deterministic evidence matching cannot occur | MEDIUM |
| `KB_DECLARED_NO_PFD` | KB description explicitly says no PFD / PFDS was provided | LOW |
| `PORTFOLIO_PLACEHOLDER_NO_PFDS` | Portfolio contains a `No_PFDS_Provided` placeholder attachment | LOW |
| `MULTIPLE_EVIDENCE_CANDIDATES` | More than one attachment matched the same KB row | MEDIUM |
| `ROW_MISSING_PORTFOLIO_REFERENCE` | KB row lacks a portfolio reference | MEDIUM |

## Current High-Severity Exceptions

High-severity exceptions are source discrepancy review candidates. These are KB rows that reference a bug / patch number but did not map to an extracted PFDS attachment in the referenced portfolio.

Current count: 10

| KB | MP | Release Date | Bug / Patch | Product | Category | Portfolio | Description |
|---|---|---|---|---|---|---|---|
| KB881136 | MP 1 | April 04, 2026 | 38983801 | Oracle Utilities Customer Care and Billing | Notification Preferences | `CCS_26.4_MP1.1.0_PFDs_Portfolio.pdf` | Notification-related Issues |
| KB881136 | MP 1 | April 04, 2026 | 39007153 | Oracle Utilities Customer Care and Billing | Customer 360 | `CCS_26.4_MP1.1.0_PFDs_Portfolio.pdf` | Additional changes to display AI-generated summary to Customer Activity History zone |
| KB881135 | MP 7 | April 04, 2026 | 38932135 | Oracle Utilities Customer to Meter | Market Transaction Messaging | `CCS_25.10_MP7.1.0_PFDs_Portfolio.pdf` | Database Health Check: Orphan Records - MTM objects and system generated imports on scripts |
| KB869018 | MP 5 | February 07, 2026 | 38889566 | Oracle Utilities Customer to Meter | Market Transaction Messaging | `CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf` | Custom Modification algorithm types cleanup |
| KB869018 | MP 5 | February 07, 2026 | 38866025 | Oracle Utilities Customer to Meter | Market Transaction Messaging | `CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf` | Incorrect value if Market Participant Type is set to 'AY' |
| KB869018 | MP 5 | February 07, 2026 | 38765800 | Oracle Utilities Customer to Meter | Market Transaction Messaging | `CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf` | Market Transaction Messages 867_03/810 non-final not RFP for service point with meter removed, 810s are stuck in 'Investigate' / 'Cancel' status |
| KB869018 | MP 5 | February 07, 2026 | 38711109 | Oracle Utilities Customer to Meter | Market Transaction Messaging | `CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf` | U2BILLGENPRC algorithm needs to be fixed to ignore adjustment only bill |
| KB869018 | MP 5 | February 07, 2026 | 38803958 | Oracle Utilities Customer to Meter | Market Transaction Messaging | `CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf` | Error upon viewing a service agreement - field name 'ACT_ERROR_MESSAGE' that does not exist |
| KB869018 | MP 5 | February 07, 2026 | 38803048 | Oracle Utilities Customer to Meter | Market Transaction Messaging | `CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf` | Various MTM transaction and zone errors |
| KB869018 | MP 5 | February 07, 2026 | 38719400 | Oracle Utilities Customer to Meter | Market Transaction Messaging | `CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf` | Remove 'Error Status' soft parameter from U2VALMM algorithm |

## Current Per-KB Exception Counts

| KB | MP | Exception Count | Breakdown |
|---|---|---:|---|
| KB881136 | MP 1 | 7 | 2 missing PFDS evidence; 3 missing fix identifier; 1 KB-declared no PFD; 1 portfolio no-PFDS placeholder |
| KB881135 | MP 7 | 1 | 1 missing PFDS evidence |
| KB869018 | MP 5 | 8 | 7 missing PFDS evidence; 1 missing fix identifier |
| KB875759 | MP 6 | 7 | 5 KB-declared no PFD; 2 missing fix identifier |

## Key Code Added During Gate 1

| Script | Purpose |
|---|---|
| `backend/app/scripts/extract_kb_source_manifest.py` | Build KB/portfolio source inventory |
| `backend/app/scripts/extract_pdf_portfolios.py` | Extract embedded portfolio child files and classify attachment metadata |
| `backend/app/scripts/extract_kb_fix_rows.py` | Parse KB HTML tables into structured fix rows |
| `backend/app/scripts/build_kb_evidence_map.py` | Join KB fix rows to extracted PFDS evidence |
| `backend/app/scripts/summarize_kb_evidence_exceptions.py` | Create structured exception summary |
| `backend/app/scripts/export_kb_evidence_exceptions_csv.py` | Export exceptions to CSV |
| `backend/app/scripts/write_kb_evidence_summary.py` | Write Markdown exception summary |
| `backend/app/scripts/run_gate1_kb_extraction.py` | Run the full Gate 1 pipeline end-to-end |

## What This Proves

Gate 1 proves that the project can now:

- read downloaded KB source pages,
- extract KB document IDs from source metadata,
- locate referenced PDF Portfolio files,
- extract embedded child PDFs from PDF Portfolios,
- hash extracted attachments,
- detect candidate bug/enhancement identifiers from attachment filenames,
- classify explicit `No_PFDS_Provided` placeholder files,
- parse KB release tables into structured rows,
- preserve product and category fields from the KB table,
- map KB rows to extracted PFDS evidence by portfolio and bug / patch number,
- separate true missing evidence from KB-declared no-PFD conditions,
- produce reviewer-facing JSON, CSV, and Markdown artifacts.

## Known Limitations

The current Gate 1 implementation is deliberately file-based and manifest-based.

Known limitations:

- It does not ingest extracted PDF text into the retrieval corpus yet.
- It does not chunk or embed child PDFs.
- It does not extract screenshots, highlights, or image context yet.
- It does not expose these artifacts in the web UI yet.
- It does not persist KB source state in the application database yet.
- It assumes downloaded KB HTML and portfolio PDFs are already available under `kbs/`.
- Row warnings remain where source KB rows omit bug / patch, product, or category data.

These limitations are acceptable for Gate 1. They define the next gate.

## Recommended Next Gate

Recommended next gate:

**Gate 2 — Source Text Extraction and Search Context**

Gate 2 should convert extracted child PDFs and KB row metadata into retrieval-ready source context artifacts.

Proposed Gate 2 sequence:

1. Extract text from all matched PFDS child PDFs.
2. Preserve source lineage:
   - KB document
   - maintenance pack
   - hot fix release date
   - portfolio file
   - child PDF
   - bug / patch number
   - product
   - category
   - description
3. Detect image-bearing pages and create source context flags.
4. Detect true PDF highlight annotations where available.
5. Write normalized `search_context` artifacts.
6. Prepare for chunking and embeddings.

Do not start with analysis generation. The next step is retrieval-ready source context.

## Recommended Next Chat Starting Point

Use this prompt to continue in a new chat:

```text
We are continuing work on the Upgrade Impact Analysis Tool.

We just completed Gate 1 of the KB source extraction/customization phase.

Use this repo as source of truth:
mcstabface/upgrade-impact-tool

Start from these docs/artifacts:
- docs/checkpoints/Gate 1 KB Source Extraction Completion Artifact.md
- kbs/manifests/kb_evidence_exception_summary.md
- kbs/manifests/kb_evidence_exceptions.csv
- backend/app/scripts/run_gate1_kb_extraction.py

Current Gate 1 status:
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

The Gate 1 pipeline runs successfully with:
python -m app.scripts.run_gate1_kb_extraction

Next recommended gate is Gate 2: Source Text Extraction and Search Context.

Please review the repo and produce the next concrete build plan and first patches for Gate 2.
Be specific, repo-grounded, and provide exact patch contents.
```

## Completion Status

Gate 1 is complete for the current source corpus.

The next work should begin from this checkpoint, not from memory.
