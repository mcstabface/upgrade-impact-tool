# KB Impact Draft Skeleton Summary

Generated UTC: `2026-05-12T14:53:19.081887+00:00`

## Overview

- Enriched context schema: `kb_impact_context.v2`
- Enriched context status: `ENRICHED_EVIDENCE_ONLY_NO_GENERATED_CLAIMS`
- Skeleton schema: `kb_impact_draft_skeleton.v1`
- Skeleton status: `STRUCTURE_ONLY_NO_GENERATED_CLAIMS`
- Evidence items: 15
- Evidence groups: 10
- Image-bearing evidence items: 15
- High-severity evidence exceptions: 10
- Skeleton sections: 8

## Generation Policy

- allowed_use: `Structure-only draft container for later reviewer-controlled impact drafting.`
- impact_claims_generated: `False`
- llm_used: `False`
- narrative_generated: `False`
- prohibited_use: `Do not treat this skeleton as impact analysis or generated conclusions.`

## Interpretation

Gate 7 enriches the evidence packet and creates a draft container. The skeleton contains sections, evidence references, and unresolved gap placeholders only. It does not contain generated impact conclusions.

## Skeleton Sections

| Section | Status | Evidence IDs | Content Present |
|---|---|---:|---|
| Scope and Inputs | STRUCTURE_ONLY_NO_GENERATED_CLAIMS | 0 | False |
| Evidence Groups | STRUCTURE_ONLY_NO_GENERATED_CLAIMS | 15 | False |
| Impacted Product Area: Oracle Utilities Customer Care and Billing | EMPTY_NO_GENERATED_CLAIMS | 5 | False |
| Impacted Product Area: Oracle Utilities Service and Measurement Data Foundation | EMPTY_NO_GENERATED_CLAIMS | 10 | False |
| Assumptions | EMPTY_NO_GENERATED_CLAIMS | 0 | False |
| Unresolved Evidence Gaps | STRUCTURE_ONLY_NO_GENERATED_CLAIMS | 0 | True |
| Reviewer Notes | EMPTY_NO_GENERATED_CLAIMS | 0 | False |
| No Generated Conclusion Status | NO_GENERATED_CONCLUSIONS | 0 | True |

## Evidence Exception Context

### Status Counts

| Status | Count |
|---|---:|
| KB explicitly declares no PFD | 6 |
| KB row missing bug / patch identifier | 6 |
| Missing extracted PFDS evidence | 10 |
| Portfolio contains no-PFDS placeholder | 1 |

### High-Severity Exceptions

| KB | MP | Bug / Patch | Product | Category | Description |
|---|---|---|---|---|---|
| KB881136 | MP 1 | 38983801 | Oracle Utilities Customer Care and Billing | Notification Preferences | Notification-related Issues |
| KB881136 | MP 1 | 39007153 | Oracle Utilities Customer Care and Billing | Customer 360 | Additional changes to display AI-generated summary to Customer Activity History zone |
| KB881135 | MP 7 | 38932135 | Oracle Utilities Customer to Meter | Market Transaction Messaging | Database Health Check: Orphan Records - MTM objects and system generated imports on scripts |
| KB869018 | MP 5 | 38889566 | Oracle Utilities Customer to Meter | Market Transaction Messaging | Custom Modification algorithm types cleanup |
| KB869018 | MP 5 | 38866025 | Oracle Utilities Customer to Meter | Market Transaction Messaging | Incorrect value if Market Participant Type is set to 'AY' |
| KB869018 | MP 5 | 38765800 | Oracle Utilities Customer to Meter | Market Transaction Messaging | Market Transaction Messages 867_03/810 non-final not RFP for service point with meter removed, 810s are stuck in 'Investigate' / 'Cancel' status |
| KB869018 | MP 5 | 38711109 | Oracle Utilities Customer to Meter | Market Transaction Messaging | U2BILLGENPRC algorithm needs to be fixed to ignore adjustment only bill |
| KB869018 | MP 5 | 38803958 | Oracle Utilities Customer to Meter | Market Transaction Messaging | Error upon viewing a service agreement - field name 'ACT_ERROR_MESSAGE' that does not exist |
| KB869018 | MP 5 | 38803048 | Oracle Utilities Customer to Meter | Market Transaction Messaging | Various MTM transaction and zone errors |
| KB869018 | MP 5 | 38719400 | Oracle Utilities Customer to Meter | Market Transaction Messaging | Remove 'Error Status' soft parameter from U2VALMM algorithm |

## PDF Context Flags

| Evidence ID | Bug / Patch | Product | Category | Has Images | Image Count | Highlights | Text Status |
|---|---|---|---|---|---:|---|---|
| 4f4cbbe012c6c61a | 39002995 | Oracle Utilities Service and Measurement Data Foundation | Usage | True | 10 | False | HAS_TEXT |
| 0bda9695e88f746c | 39007114 | Oracle Utilities Service and Measurement Data Foundation | Usage | True | 10 | False | HAS_TEXT |
| 4f36e7a253467768 | 39127058 | Oracle Utilities Service and Measurement Data Foundation | Usage | True | 8 | False | HAS_TEXT |
| c8146663783b1ce0 | 38794940 | Oracle Utilities Service and Measurement Data Foundation | Usage | True | 9 | False | HAS_TEXT |
| e1e70f018e26be2d | 38966530 | Oracle Utilities Service and Measurement Data Foundation | Usage | True | 8 | False | HAS_TEXT |
| 603547a634443bcb | 38848234 | Oracle Utilities Customer Care and Billing | Billing | True | 234 | False | HAS_TEXT |
| 970bbd743c307ff2 | 39234264 | Oracle Utilities Customer Care and Billing | Billing | True | 20 | False | HAS_TEXT |
| 1cc8cb7c3db849f3 | 39064768 | Oracle Utilities Customer Care and Billing | Conversion | True | 42 | False | HAS_TEXT |
| 71db8e4fa7f2b8e5 | 38959224 | Oracle Utilities Customer Care and Billing | Case Management | True | 81 | False | HAS_TEXT |
| fbd5fab7e7286d4e | 38959233 | Oracle Utilities Customer Care and Billing | Case Management | True | 90 | False | HAS_TEXT |
| ba55538e4b6a1e3b | 38794940 | Oracle Utilities Service and Measurement Data Foundation | Usage | True | 9 | False | HAS_TEXT |
| 1ca0f8c396010bcd | 39127058 | Oracle Utilities Service and Measurement Data Foundation | Usage | True | 8 | False | HAS_TEXT |
| d5ebe5a7d15fc41d | 39002995 | Oracle Utilities Service and Measurement Data Foundation | Usage | True | 10 | False | HAS_TEXT |
| 9b0ce46be6dfb22c | 39007114 | Oracle Utilities Service and Measurement Data Foundation | Usage | True | 10 | False | HAS_TEXT |
| 7660d8480f7219d5 | 38966530 | Oracle Utilities Service and Measurement Data Foundation | Usage | True | 8 | False | HAS_TEXT |

## Source Inputs

- eval_results_path: `kbs/manifests/kb_retrieval_eval_results.json`
- exception_summary_path: `kbs/manifests/kb_evidence_exception_summary.md`
- index_path: `kbs/indexes/kb_chunk_lexical_index.sqlite`
- max_results_per_case: `5`
- output_path: `kbs/impact_context/kb_impact_context.v2.enriched.json`
- search_context_manifest_path: `kbs/manifests/kb_search_context_manifest.json`
- source_context_path: `kbs/impact_context/kb_impact_context.v1.json`
