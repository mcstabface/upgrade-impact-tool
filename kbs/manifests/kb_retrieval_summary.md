# KB PFDS Retrieval Summary

Generated UTC: `2026-05-12T14:03:26.320864+00:00`

## Overview

- Source chunk collections: 179
- Indexed collections: 179
- Source chunks: 895
- Indexed chunks: 895
- Posting rows: 79073
- Vocabulary size: 4857
- Index path: `kbs/indexes/kb_chunk_lexical_index.sqlite`
- Source chunk manifest: `kbs/manifests/kb_search_context_chunks_manifest.json`
- Index failures: 0

## Interpretation

Gate 3 builds deterministic lexical retrieval over Gate 2 PFDS chunks. The index is a retrieval substrate only; it does not generate upgrade impact analysis or infer business truth. Every returned chunk remains tied to KB, portfolio, child PDF, and bug/patch lineage.

## Per-KB Index Breakdown

| KB | Collections | Indexed Chunks | Tokens |
|---|---:|---:|---:|
| KB869018 | 34 | 164 | 29671 |
| KB875759 | 56 | 306 | 55296 |
| KB881135 | 35 | 179 | 31166 |
| KB881136 | 54 | 246 | 42918 |

## Product Breakdown

| Product | Collections | Indexed Chunks |
|---|---:|---:|
| Oracle Utilities Framework | 55 | 158 |
| Oracle Utilities Customer Care and Billing | 53 | 390 |
| Oracle Utilities Service and Measurement Data Foundation | 47 | 244 |
| Oracle Utilities Customer to Meter | 18 | 77 |
| Oracle Utilities Cloud Service Foundation | 4 | 17 |
| Oracle Utilities Asset Management Base | 2 | 9 |

## Category Breakdown

| Category | Collections | Indexed Chunks |
|---|---:|---:|
| Usage | 20 | 117 |
| System Wide | 11 | 43 |
| General | 10 | 30 |
| Digital Asset Management | 8 | 35 |
| Rates | 8 | 120 |
| Database | 7 | 23 |
| Batch | 6 | 18 |
| Cloud Infrastructure | 6 | 16 |
| Billing | 5 | 34 |
| Customer Information | 5 | 23 |
| Usage Rules | 5 | 31 |
| Case Management | 4 | 18 |
| Cloud Service Foundation | 4 | 17 |
| Conversion | 4 | 32 |
| Measurement | 4 | 12 |
| Meter Data Management | 4 | 13 |
| User Interface | 4 | 13 |
| Cloud infrastructure | 3 | 8 |
| Communications | 3 | 17 |
| Credit and Collection | 3 | 19 |
| For SGG specific Functionality | 3 | 11 |
| Security | 3 | 10 |
| Start/Stop/Transfer | 3 | 13 |
| Third Party Software | 3 | 6 |
| To Do | 3 | 13 |
| Web Self Service | 3 | 23 |
| Accessibility | 2 | 21 |
| Assets | 2 | 9 |
| Configuration Tools | 2 | 6 |
| Digital Asset | 2 | 13 |
| For MDM specific Functionality | 2 | 7 |
| Implementation Tools | 2 | 6 |
| Payment | 2 | 13 |
| REST APIs | 2 | 13 |
| To Do Management | 2 | 9 |
| 360 Degree Search and View | 1 | 4 |
| Adjustments | 1 | 5 |
| BI Extracts | 1 | 5 |
| Budgets | 1 | 4 |
| Common | 1 | 4 |
| Control Central | 1 | 4 |
| Cross-Product Maintenance | 1 | 3 |
| Customer 360 | 1 | 4 |
| Documentation | 1 | 2 |
| Environment | 1 | 4 |
| Inbound Web Service | 1 | 8 |
| Release, Patches, Env Scripts | 1 | 3 |
| Service Order Management | 1 | 4 |
| Sliver Spring Networks | 1 | 6 |
| Sync Request | 1 | 6 |
| Undetermined | 1 | 4 |
| Unknown / No Component | 1 | 3 |
| VEE | 1 | 4 |
| [ORGANIZATION] | 1 | 6 |

## Token-Heavy Collections

| KB | Bug / Patch | Product | Category | Indexed Chunks | Tokens | Collection |
|---|---|---|---|---:|---:|---|
| KB875759 | 38558279 | Oracle Utilities Customer Care and Billing | Rates | 37 | 7086 | `kbs/search_context_chunks/KB875759/KB875759__38558279__CCS_25.10_MP6.2.2_PFDs_Portfolio.pdf__cc25ac27bf77__chunks.json` |
| KB881136 | 39020780 | Oracle Utilities Customer Care and Billing | Rates | 35 | 6866 | `kbs/search_context_chunks/KB881136/KB881136__39020780__CCS_26.4_MP1.3.3_PFDs_Portfolio.pdf__f4a9a9a677a2__chunks.json` |
| KB875759 | 38664105 | Oracle Utilities Customer Care and Billing | Web Self Service | 17 | 3336 | `kbs/search_context_chunks/KB875759/KB875759__38664105__CCS_25.10_MP6.1.0_PFDs_Portfolio.pdf__f0427d5733f2__chunks.json` |
| KB869018 | 38746273 | Oracle Utilities Customer Care and Billing | Accessibility | 15 | 3324 | `kbs/search_context_chunks/KB869018/KB869018__38746273__CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf__194aa5e05e8c__chunks.json` |
| KB869018 | 38799961 | Oracle Utilities Customer Care and Billing | Conversion | 12 | 2411 | `kbs/search_context_chunks/KB869018/KB869018__38799961__CCS_25.10_MP5.1.0_PFDs_Portfolio.pdf__aca76d2fcc95__chunks.json` |
| KB881136 | 39003305 | Oracle Utilities Customer Care and Billing | Rates | 11 | 2158 | `kbs/search_context_chunks/KB881136/KB881136__39003305__CCS_26.4_MP1.4.0_PFDs_Portfolio.pdf__3e9c41e761b6__chunks.json` |
| KB875759 | 38742668 | Oracle Utilities Customer Care and Billing | Rates | 11 | 2157 | `kbs/search_context_chunks/KB875759/KB875759__38742668__CCS_25.10_MP6.1.0_PFDs_Portfolio.pdf__4baace5b900b__chunks.json` |
| KB881135 | 39064768 | Oracle Utilities Customer Care and Billing | Conversion | 10 | 2100 | `kbs/search_context_chunks/KB881135/KB881135__39064768__CCS_25.10_MP7.4.1_PFDs_Portfolio.pdf__426d44e375aa__chunks.json` |
| KB881136 | 39007114 | Oracle Utilities Service and Measurement Data Foundation | Usage | 9 | 1822 | `kbs/search_context_chunks/KB881136/KB881136__39007114__CCS_26.4_MP1.1.0_PFDs_Portfolio.pdf__c7e0e1085aae__chunks.json` |
| KB875759 | 39002995 | Oracle Utilities Service and Measurement Data Foundation | Usage | 9 | 1821 | `kbs/search_context_chunks/KB875759/KB875759__39002995__CCS_25.10_MP6.2.2_PFDs_Portfolio.pdf__782dd1bd928a__chunks.json` |

## Latest Smoke Query

- Query artifact: `/home/stabby/Documents/upgrade-impact-tool/kbs/query_context/rates_billing_usage__9ada4c1a54049658.query_context.json`
- Query text: `rates billing usage`
- Query terms: `rates, billing, usage`
- Candidate chunks: 504
- Scored chunks: 504
- Returned chunks: 5
- Ranker: `term_frequency_idf_v1`

| Rank | Score | KB | Bug / Patch | Product | Category | Matched Terms |
|---:|---:|---|---|---|---|---|
| 1 | 68.70211 | KB881135 | 39109281 | Oracle Utilities Service and Measurement Data Foundation | Usage Rules | usage |
| 2 | 65.954026 | KB875759 | 38884483 | Oracle Utilities Service and Measurement Data Foundation | Usage Rules | usage |
| 3 | 65.954026 | KB881135 | 39187679 | Oracle Utilities Service and Measurement Data Foundation | Usage | usage |
| 4 | 63.205941 | KB875759 | 38884483 | Oracle Utilities Service and Measurement Data Foundation | Usage Rules | usage |
| 5 | 61.145076 | KB875759 | 39002995 | Oracle Utilities Service and Measurement Data Foundation | Usage | rates, usage |
