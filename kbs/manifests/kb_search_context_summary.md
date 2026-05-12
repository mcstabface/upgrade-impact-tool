# KB Search Context Summary

Generated UTC: `2026-05-12T13:43:47.795443+00:00`

## Overview

- Matched PFDS evidence rows: 179
- Search-context artifacts: 179
- Text extraction failures: 0
- Empty-text artifacts: 0
- Image-bearing artifacts: 178
- Highlight-bearing artifacts: 0
- Chunk collections: 179
- Chunks: 895
- Chunking skipped empty-text artifacts: 0
- Chunking failures: 0

## Interpretation

Gate 2 materializes matched PFDS evidence into retrieval-ready source context and deterministic chunks. This is still source preparation, not upgrade impact analysis. The artifacts preserve KB and PFDS lineage so later retrieval, review, and analysis can point back to source evidence.

Image-bearing artifacts indicate PFDS documents whose extracted text may not capture all visual information. These should remain visible for reviewer awareness before relying on text-only retrieval.

## Per-KB Breakdown

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

## Category Breakdown

| Category | Search-Context Artifacts |
|---|---:|
| Usage | 20 |
| System Wide | 11 |
| General | 10 |
| Digital Asset Management | 8 |
| Rates | 8 |
| Database | 7 |
| Batch | 6 |
| Cloud Infrastructure | 6 |
| Billing | 5 |
| Customer Information | 5 |
| Usage Rules | 5 |
| Case Management | 4 |
| Cloud Service Foundation | 4 |
| Conversion | 4 |
| Measurement | 4 |
| Meter Data Management | 4 |
| User Interface | 4 |
| Cloud infrastructure | 3 |
| Communications | 3 |
| Credit and Collection | 3 |
| For SGG specific Functionality | 3 |
| Security | 3 |
| Start/Stop/Transfer | 3 |
| Third Party Software | 3 |
| To Do | 3 |
| Web Self Service | 3 |
| Accessibility | 2 |
| Assets | 2 |
| Configuration Tools | 2 |
| Digital Asset | 2 |
| For MDM specific Functionality | 2 |
| Implementation Tools | 2 |
| Payment | 2 |
| REST APIs | 2 |
| To Do Management | 2 |
| 360 Degree Search and View | 1 |
| Adjustments | 1 |
| BI Extracts | 1 |
| Budgets | 1 |
| Common | 1 |
| Control Central | 1 |
| Cross-Product Maintenance | 1 |
| Customer 360 | 1 |
| Documentation | 1 |
| Environment | 1 |
| Inbound Web Service | 1 |
| Release, Patches, Env Scripts | 1 |
| Service Order Management | 1 |
| Sliver Spring Networks | 1 |
| Sync Request | 1 |
| Undetermined | 1 |
| Unknown / No Component | 1 |
| VEE | 1 |
| [ORGANIZATION] | 1 |

## Top Image-Heavy PFDS Artifacts

| KB | Bug / Patch | Product | Category | Images | Pages | Child PDF |
|---|---|---|---|---:|---:|---|
| KB869018 | 38746273 | Oracle Utilities Customer Care and Billing | Accessibility | 500 | 25 | `kbs/extracted/CCS_25.10_MP5.1.0_PFDs_Portfolio/0_Bug_38746273_Product_Fix_Design_6.pdf` |
| KB875759 | 38558279 | Oracle Utilities Customer Care and Billing | Rates | 410 | 41 | `kbs/extracted/CCS_25.10_MP6.2.2_PFDs_Portfolio/0_Bug_38558279_Product_Fix_Design_6.pdf` |
| KB881136 | 39020780 | Oracle Utilities Customer Care and Billing | Rates | 380 | 38 | `kbs/extracted/CCS_26.4_MP1.3.3_PFDs_Portfolio/0_Bug_39020780_Product_Fix_Design_6.pdf` |
| KB869018 | 38848234 | Oracle Utilities Customer Care and Billing | Billing | 234 | 13 | `kbs/extracted/CCS_25.10_MP5.3.1_PFDs_Portfolio/0_Bug_38848234_Product_Fix_Design_6.pdf` |
| KB875759 | 38900687 | Oracle Utilities Customer Care and Billing | To Do | 225 | 15 | `kbs/extracted/CCS_25.10_MP6.1.0_PFDs_Portfolio/0_Bug_38900687_Product_Fix_Design_6.pdf` |
| KB869018 | 38864954 | Oracle Utilities Customer Care and Billing | Customer Information | 224 | 14 | `kbs/extracted/CCS_25.10_MP5.1.0_PFDs_Portfolio/0_Bug_38864954_Product_Fix_Design_6.pdf` |
| KB875759 | 38743538 | Oracle Utilities Customer Care and Billing | Credit and Collection | 210 | 15 | `kbs/extracted/CCS_25.10_MP6.1.0_PFDs_Portfolio/0_Bug_38743538_Product_Fix_Design_6.pdf` |
| KB875759 | 38664105 | Oracle Utilities Customer Care and Billing | Web Self Service | 198 | 22 | `kbs/extracted/CCS_25.10_MP6.1.0_PFDs_Portfolio/0_Bug_38664105_Product_Fix_Design_6.pdf` |
| KB875759 | 38410113 | Oracle Utilities Customer Care and Billing | System Wide | 168 | 14 | `kbs/extracted/CCS_25.10_MP6.1.0_PFDs_Portfolio/0_Bug_38410113_Product_Fix_Design_6.pdf` |
| KB881135 | 39068627 | Oracle Utilities Customer to Meter | Sync Request | 156 | 13 | `kbs/extracted/CCS_25.10_MP7.5.0_PFDs_Portfolio/0_Bug_39068627_Product_Fix_Design_6.pdf` |

## Largest Chunk Collections

| KB | Bug / Patch | Product | Category | Chunks | Source Chars | Collection |
|---|---|---|---|---:|---:|---|
| KB875759 | 38558279 | Oracle Utilities Customer Care and Billing | Rates | 37 | 65528 | `kbs/search_context_chunks/KB875759/KB875759__38558279__CCS_25.10_MP6.2.2_PFDs_Portfolio.pdf__cc25ac27bf77__chunks.json` |
| KB881136 | 39020780 | Oracle Utilities Customer Care and Billing | Rates | 35 | 63127 | `kbs/search_context_chunks/KB881136/KB881136__39020780__CCS_26.4_MP1.3.3_PFDs_Portfolio.pdf__f4a9a9a677a2__chunks.json` |
| KB875759 | 38664105 | Oracle Utilities Customer Care and Billing | Web Self Service | 17 | 29893 | `kbs/search_context_chunks/KB875759/KB875759__38664105__CCS_25.10_MP6.1.0_PFDs_Portfolio.pdf__f0427d5733f2__chunks.json` |
| KB869018 | 38746273 | Oracle Utilities Customer Care and Billing | Accessibility | 15 | 26156 | `kbs/search_context_chunks/KB869018/KB869018__38746273__CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf__194aa5e05e8c__chunks.json` |
| KB869018 | 38799961 | Oracle Utilities Customer Care and Billing | Conversion | 12 | 20943 | `kbs/search_context_chunks/KB869018/KB869018__38799961__CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf__aca76d2fcc95__chunks.json` |
| KB875759 | 38742668 | Oracle Utilities Customer Care and Billing | Rates | 11 | 19467 | `kbs/search_context_chunks/KB875759/KB875759__38742668__CCS_25.10_MP6.1.0_PFDs_Portfolio.pdf__4baace5b900b__chunks.json` |
| KB881136 | 39003305 | Oracle Utilities Customer Care and Billing | Rates | 11 | 19464 | `kbs/search_context_chunks/KB881136/KB881136__39003305__CCS_26.4_MP1.4.0_PFDs_Portfolio.pdf__3e9c41e761b6__chunks.json` |
| KB881135 | 39064768 | Oracle Utilities Customer Care and Billing | Conversion | 10 | 17979 | `kbs/search_context_chunks/KB881135/KB881135__39064768__CCS_25.10_MP7.4.1_PFDs_Portfolio.pdf__426d44e375aa__chunks.json` |
| KB875759 | 38410113 | Oracle Utilities Customer Care and Billing | System Wide | 9 | 15537 | `kbs/search_context_chunks/KB875759/KB875759__38410113__CCS_25.10_MP6.1.0_PFDs_Portfolio.pdf__d8428b626d30__chunks.json` |
| KB881135 | 38950205 | Oracle Utilities Service and Measurement Data Foundation | Communications | 9 | 14927 | `kbs/search_context_chunks/KB881135/KB881135__38950205__CCS_25.10_MP7.1.0_PFDs_Portfolio.pdf__674157aa8f96__chunks.json` |

## Manifest Inputs

- Text manifest: `kbs/manifests/kb_evidence_map.json`
- Chunk source manifest: `kbs/manifests/kb_search_context_manifest.json`
- Chunk output root: `kbs/search_context_chunks`

## Warnings

- Text extraction: One or more search context artifacts contain image-bearing pages that may need visual review.
