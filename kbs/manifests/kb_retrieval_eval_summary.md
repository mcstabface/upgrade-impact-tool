# KB Retrieval Evaluation Summary

Generated UTC: `2026-05-12T14:35:38.784225+00:00`

## Overview

- Evaluation set: `kbs/eval/kb_retrieval_eval_set.json`
- Index path: `kbs/indexes/kb_chunk_lexical_index.sqlite`
- Cases: 3
- Passed: 3
- Failed: 0

## Case Results

| Case | Status | Query | Ranker | Returned | Failures |
|---|---|---|---|---:|---|
| usage_rates_unfiltered_bm25 | PASS | rates billing usage | bm25_v1 | 5 |  |
| billing_usage_filtered_ccb_bm25 | PASS | rates billing usage | bm25_v1 | 5 |  |
| rates_filtered_smdf_usage_bm25 | PASS | rates | bm25_v1 | 5 |  |

## Top Results by Case

### usage_rates_unfiltered_bm25

| Rank | Score | KB | Bug / Patch | Product | Category | Matched Terms |
|---:|---:|---|---|---|---|---|
| 1 | 8.97746 | KB875759 | 39002995 | Oracle Utilities Service and Measurement Data Foundation | Usage | billing, rates, usage |
| 2 | 8.97746 | KB881136 | 39007114 | Oracle Utilities Service and Measurement Data Foundation | Usage | billing, rates, usage |
| 3 | 8.016685 | KB881135 | 39127058 | Oracle Utilities Service and Measurement Data Foundation | Usage | rates, usage |
| 4 | 7.735204 | KB875759 | 38794940 | Oracle Utilities Service and Measurement Data Foundation | Usage | rates, usage |
| 5 | 6.779924 | KB881136 | 38966530 | Oracle Utilities Service and Measurement Data Foundation | Usage | rates, usage |

### billing_usage_filtered_ccb_bm25

| Rank | Score | KB | Bug / Patch | Product | Category | Matched Terms |
|---:|---:|---|---|---|---|---|
| 1 | 4.557985 | KB869018 | 38848234 | Oracle Utilities Customer Care and Billing | Billing | billing, usage |
| 2 | 4.498597 | KB881135 | 39234264 | Oracle Utilities Customer Care and Billing | Billing | billing, usage |
| 3 | 4.477924 | KB881135 | 39064768 | Oracle Utilities Customer Care and Billing | Conversion | billing, usage |
| 4 | 4.324562 | KB881135 | 38959224 | Oracle Utilities Customer Care and Billing | Case Management | billing, usage |
| 5 | 4.324562 | KB881136 | 38959233 | Oracle Utilities Customer Care and Billing | Case Management | billing, usage |

### rates_filtered_smdf_usage_bm25

| Rank | Score | KB | Bug / Patch | Product | Category | Matched Terms |
|---:|---:|---|---|---|---|---|
| 1 | 4.639323 | KB875759 | 38794940 | Oracle Utilities Service and Measurement Data Foundation | Usage | rates |
| 2 | 4.450069 | KB881135 | 39127058 | Oracle Utilities Service and Measurement Data Foundation | Usage | rates |
| 3 | 4.411156 | KB875759 | 39002995 | Oracle Utilities Service and Measurement Data Foundation | Usage | rates |
| 4 | 4.411156 | KB881136 | 39007114 | Oracle Utilities Service and Measurement Data Foundation | Usage | rates |
| 5 | 3.489463 | KB881136 | 38966530 | Oracle Utilities Service and Measurement Data Foundation | Usage | rates |
