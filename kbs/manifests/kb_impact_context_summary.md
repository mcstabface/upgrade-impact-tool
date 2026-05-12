# KB Impact Context Summary

Generated UTC: `2026-05-12T14:45:02.019031+00:00`

## Overview

- Artifact type: `kb_impact_context`
- Schema version: `kb_impact_context.v1`
- Assembly status: `EVIDENCE_ONLY_NO_GENERATED_CLAIMS`
- Evidence items: 15
- Evidence groups: 10
- Unique bug / patch numbers: 10
- Unique child PDFs: 10
- Warnings: 0

## Generation Policy

- LLM used: False
- Impact claims generated: False
- Summaries generated: False
- Allowed use: Evidence packet for reviewer inspection and later constrained impact-draft generation.
- Prohibited use: Do not treat this artifact as an impact analysis or business conclusion.

## Interpretation

This artifact is an evidence packet only. It assembles retrieved PFDS chunks, scores, and KB/PFDS lineage for reviewer inspection and later constrained impact-draft generation. It contains no generated impact analysis.

## Evidence by Evaluation Case

| Case | Evidence Items |
|---|---:|
| billing_usage_filtered_ccb_bm25 | 5 |
| rates_filtered_smdf_usage_bm25 | 5 |
| usage_rates_unfiltered_bm25 | 5 |

## Product Breakdown

| Product | Evidence Items |
|---|---:|
| Oracle Utilities Service and Measurement Data Foundation | 10 |
| Oracle Utilities Customer Care and Billing | 5 |

## Category Breakdown

| Category | Evidence Items |
|---|---:|
| Usage | 10 |
| Billing | 2 |
| Case Management | 2 |
| Conversion | 1 |

## Evidence Groups

| Group | KB | Bug / Patch | Product | Category | Evidence Count | Max Score | Child PDFs |
|---|---|---|---|---|---:|---:|---:|
| KB875759::39002995::Oracle Utilities Service and Measurement Data Foundation::Usage | KB875759 | 39002995 | Oracle Utilities Service and Measurement Data Foundation | Usage | 2 | 8.97746 | 1 |
| KB881136::39007114::Oracle Utilities Service and Measurement Data Foundation::Usage | KB881136 | 39007114 | Oracle Utilities Service and Measurement Data Foundation | Usage | 2 | 8.97746 | 1 |
| KB881135::39127058::Oracle Utilities Service and Measurement Data Foundation::Usage | KB881135 | 39127058 | Oracle Utilities Service and Measurement Data Foundation | Usage | 2 | 8.016685 | 1 |
| KB875759::38794940::Oracle Utilities Service and Measurement Data Foundation::Usage | KB875759 | 38794940 | Oracle Utilities Service and Measurement Data Foundation | Usage | 2 | 7.735204 | 1 |
| KB881136::38966530::Oracle Utilities Service and Measurement Data Foundation::Usage | KB881136 | 38966530 | Oracle Utilities Service and Measurement Data Foundation | Usage | 2 | 6.779924 | 1 |
| KB869018::38848234::Oracle Utilities Customer Care and Billing::Billing | KB869018 | 38848234 | Oracle Utilities Customer Care and Billing | Billing | 1 | 4.557985 | 1 |
| KB881135::39234264::Oracle Utilities Customer Care and Billing::Billing | KB881135 | 39234264 | Oracle Utilities Customer Care and Billing | Billing | 1 | 4.498597 | 1 |
| KB881135::39064768::Oracle Utilities Customer Care and Billing::Conversion | KB881135 | 39064768 | Oracle Utilities Customer Care and Billing | Conversion | 1 | 4.477924 | 1 |
| KB881135::38959224::Oracle Utilities Customer Care and Billing::Case Management | KB881135 | 38959224 | Oracle Utilities Customer Care and Billing | Case Management | 1 | 4.324562 | 1 |
| KB881136::38959233::Oracle Utilities Customer Care and Billing::Case Management | KB881136 | 38959233 | Oracle Utilities Customer Care and Billing | Case Management | 1 | 4.324562 | 1 |

## Top Evidence Items

| Case | Rank | Score | KB | Bug / Patch | Product | Category | Chunk |
|---|---:|---:|---|---|---|---|---|
| billing_usage_filtered_ccb_bm25 | 1 | 4.557985 | KB869018 | 38848234 | Oracle Utilities Customer Care and Billing | Billing | `KB869018::38848234::2ac533785e535054e032320967db5c36f6991d48021825a88a4d5bce8d9f89a0::0003` |
| billing_usage_filtered_ccb_bm25 | 2 | 4.498597 | KB881135 | 39234264 | Oracle Utilities Customer Care and Billing | Billing | `KB881135::39234264::c7242dc17a486aa18fde33a4e1906022748240eb19dde9d0a5b3b04b0b5e0f84::0005` |
| billing_usage_filtered_ccb_bm25 | 3 | 4.477924 | KB881135 | 39064768 | Oracle Utilities Customer Care and Billing | Conversion | `KB881135::39064768::426d44e375aa6c02d137e52c665b4006f4bd0348738635ec7963e6243ef1ad4e::0003` |
| billing_usage_filtered_ccb_bm25 | 4 | 4.324562 | KB881135 | 38959224 | Oracle Utilities Customer Care and Billing | Case Management | `KB881135::38959224::2dce6ee4ad2c1ced52097cb2a8929a80d58209de565d79977b489c8732167ca1::0001` |
| billing_usage_filtered_ccb_bm25 | 5 | 4.324562 | KB881136 | 38959233 | Oracle Utilities Customer Care and Billing | Case Management | `KB881136::38959233::00b123613330844ef1a316a48af09673243150d999b26b2f613665a156ecb479::0001` |
| rates_filtered_smdf_usage_bm25 | 1 | 4.639323 | KB875759 | 38794940 | Oracle Utilities Service and Measurement Data Foundation | Usage | `KB875759::38794940::5778c1098db572c3169b864f63675e17c5f1d68142e224502e279d4484e0203d::0004` |
| rates_filtered_smdf_usage_bm25 | 2 | 4.450069 | KB881135 | 39127058 | Oracle Utilities Service and Measurement Data Foundation | Usage | `KB881135::39127058::f5959386c0f4d87ca9473dc8ab104739e42a3ed3b3b05d60127d78f3d81a6674::0004` |
| rates_filtered_smdf_usage_bm25 | 3 | 4.411156 | KB875759 | 39002995 | Oracle Utilities Service and Measurement Data Foundation | Usage | `KB875759::39002995::782dd1bd928ad04b242485cc9d6bb0a305bb199e62bd42a09aaa0c70880ec68b::0006` |
| rates_filtered_smdf_usage_bm25 | 4 | 4.411156 | KB881136 | 39007114 | Oracle Utilities Service and Measurement Data Foundation | Usage | `KB881136::39007114::c7e0e1085aae05331b447fe98e78216a48f3909404c93d02d0ea56d7ea5e99ee::0006` |
| rates_filtered_smdf_usage_bm25 | 5 | 3.489463 | KB881136 | 38966530 | Oracle Utilities Service and Measurement Data Foundation | Usage | `KB881136::38966530::49006a8f0a51e0da7b55fb68fe1de172597f0ec356b7cfcf0d5dc8da1522337e::0005` |
| usage_rates_unfiltered_bm25 | 1 | 8.97746 | KB875759 | 39002995 | Oracle Utilities Service and Measurement Data Foundation | Usage | `KB875759::39002995::782dd1bd928ad04b242485cc9d6bb0a305bb199e62bd42a09aaa0c70880ec68b::0002` |
| usage_rates_unfiltered_bm25 | 2 | 8.97746 | KB881136 | 39007114 | Oracle Utilities Service and Measurement Data Foundation | Usage | `KB881136::39007114::c7e0e1085aae05331b447fe98e78216a48f3909404c93d02d0ea56d7ea5e99ee::0002` |
| usage_rates_unfiltered_bm25 | 3 | 8.016685 | KB881135 | 39127058 | Oracle Utilities Service and Measurement Data Foundation | Usage | `KB881135::39127058::f5959386c0f4d87ca9473dc8ab104739e42a3ed3b3b05d60127d78f3d81a6674::0004` |
| usage_rates_unfiltered_bm25 | 4 | 7.735204 | KB875759 | 38794940 | Oracle Utilities Service and Measurement Data Foundation | Usage | `KB875759::38794940::5778c1098db572c3169b864f63675e17c5f1d68142e224502e279d4484e0203d::0004` |
| usage_rates_unfiltered_bm25 | 5 | 6.779924 | KB881136 | 38966530 | Oracle Utilities Service and Measurement Data Foundation | Usage | `KB881136::38966530::49006a8f0a51e0da7b55fb68fe1de172597f0ec356b7cfcf0d5dc8da1522337e::0005` |

## Source Inputs

- eval_results_path: `kbs/manifests/kb_retrieval_eval_results.json`
- index_path: `kbs/indexes/kb_chunk_lexical_index.sqlite`
- max_results_per_case: `5`
- output_path: `kbs/impact_context/kb_impact_context.v1.json`
