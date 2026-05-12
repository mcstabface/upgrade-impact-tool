# KB BM25 Comparison Summary

Generated UTC: `2026-05-12T14:32:07.289695+00:00`

## Overview

- Query context root: `/home/stabby/Documents/upgrade-impact-tool/kbs/query_context`
- Query contexts inspected: 8
- Comparable TF-IDF/BM25 pairs: 2

## Interpretation

Gate 5 compares deterministic TF-IDF and BM25 retrieval results over the same indexed PFDS chunks. This report shows whether BM25 changes top-ranked evidence before any downstream upgrade-impact analysis consumes retrieval output.

## Comparison: `rates billing usage`

- Filters: `{"product": "Oracle Utilities Customer Care and Billing"}`
- Shared top-result chunks: 3
- TF-IDF top chunk: `KB881135::39064768::426d44e375aa6c02d137e52c665b4006f4bd0348738635ec7963e6243ef1ad4e::0003`
- BM25 top chunk: `KB869018::38848234::2ac533785e535054e032320967db5c36f6991d48021825a88a4d5bce8d9f89a0::0003`

| Rank | TF-IDF Chunk | BM25 Chunk | Same Chunk |
|---:|---|---|---|
| 1 | `KB881135::39064768::426d44e375aa6c02d137e52c665b4006f4bd0348738635ec7963e6243ef1ad4e::0003` | `KB869018::38848234::2ac533785e535054e032320967db5c36f6991d48021825a88a4d5bce8d9f89a0::0003` | False |
| 2 | `KB881135::39234264::c7242dc17a486aa18fde33a4e1906022748240eb19dde9d0a5b3b04b0b5e0f84::0005` | `KB881135::39234264::c7242dc17a486aa18fde33a4e1906022748240eb19dde9d0a5b3b04b0b5e0f84::0005` | True |
| 3 | `KB869018::38848234::2ac533785e535054e032320967db5c36f6991d48021825a88a4d5bce8d9f89a0::0003` | `KB881135::39064768::426d44e375aa6c02d137e52c665b4006f4bd0348738635ec7963e6243ef1ad4e::0003` | False |
| 4 | `KB881135::38959224::2dce6ee4ad2c1ced52097cb2a8929a80d58209de565d79977b489c8732167ca1::0003` | `KB881135::38959224::2dce6ee4ad2c1ced52097cb2a8929a80d58209de565d79977b489c8732167ca1::0001` | False |
| 5 | `KB881136::38959233::00b123613330844ef1a316a48af09673243150d999b26b2f613665a156ecb479::0003` | `KB881136::38959233::00b123613330844ef1a316a48af09673243150d999b26b2f613665a156ecb479::0001` | False |

### tfidf_v1: `rates_billing_usage__9ada4c1a54049658__401a4827ce310816.query_context.json`

- Returned: 5
- Candidate chunks: 373
- Post-diversity scored chunks: 53

| Rank | Score | KB | Bug / Patch | Product | Category | Matched Terms | Contributions |
|---:|---:|---|---|---|---|---|---|
| 1 | 42.116361 | KB881135 | 39064768 | Oracle Utilities Customer Care and Billing | Conversion | billing, usage | billing:3.643179, usage:38.473182 |
| 2 | 31.124023 | KB881135 | 39234264 | Oracle Utilities Customer Care and Billing | Billing | billing, usage | billing:3.643179, usage:27.480844 |
| 3 | 29.271033 | KB869018 | 38848234 | Oracle Utilities Customer Care and Billing | Billing | billing, usage | billing:7.286358, usage:21.984675 |
| 4 | 22.87977 | KB881135 | 38959224 | Oracle Utilities Customer Care and Billing | Case Management | billing, usage | billing:3.643179, usage:19.236591 |
| 5 | 21.05818 | KB881136 | 38959233 | Oracle Utilities Customer Care and Billing | Case Management | billing, usage | billing:1.82159, usage:19.236591 |

### bm25_v1: `rates_billing_usage__9ada4c1a54049658__cae3de743c71ae19.query_context.json`

- Returned: 5
- Candidate chunks: 373
- Post-diversity scored chunks: 53
- BM25 k1: 1.2
- BM25 b: 0.75
- Average document length: 177.710615

| Rank | Score | KB | Bug / Patch | Product | Category | Matched Terms | Contributions |
|---:|---:|---|---|---|---|---|---|
| 1 | 4.557985 | KB869018 | 38848234 | Oracle Utilities Customer Care and Billing | Billing | billing, usage | billing:1.3153, usage:3.242684 |
| 2 | 4.498597 | KB881135 | 39234264 | Oracle Utilities Customer Care and Billing | Billing | billing, usage | billing:1.092879, usage:3.405718 |
| 3 | 4.477924 | KB881135 | 39064768 | Oracle Utilities Customer Care and Billing | Conversion | billing, usage | billing:1.013837, usage:3.464087 |
| 4 | 4.324562 | KB881135 | 38959224 | Oracle Utilities Customer Care and Billing | Case Management | billing, usage | billing:1.382398, usage:2.942163 |
| 5 | 4.324562 | KB881136 | 38959233 | Oracle Utilities Customer Care and Billing | Case Management | billing, usage | billing:1.382398, usage:2.942163 |

## Comparison: `rates billing usage`

- Filters: `{}`
- Shared top-result chunks: 0
- TF-IDF top chunk: `KB881135::39109281::c47e693c88ab2fb1d7b10170c77bc18b894e99d7eaa1b568bc3cb9a5d3418cb5::0004`
- BM25 top chunk: `KB875759::39002995::782dd1bd928ad04b242485cc9d6bb0a305bb199e62bd42a09aaa0c70880ec68b::0002`

| Rank | TF-IDF Chunk | BM25 Chunk | Same Chunk |
|---:|---|---|---|
| 1 | `KB881135::39109281::c47e693c88ab2fb1d7b10170c77bc18b894e99d7eaa1b568bc3cb9a5d3418cb5::0004` | `KB875759::39002995::782dd1bd928ad04b242485cc9d6bb0a305bb199e62bd42a09aaa0c70880ec68b::0002` | False |
| 2 | `KB875759::38884483::4bd869477b2f9772ef0dd9f07b10e4e3ab7c55d19d881885e7b51768200bf649::0004` | `KB881136::39007114::c7e0e1085aae05331b447fe98e78216a48f3909404c93d02d0ea56d7ea5e99ee::0002` | False |
| 3 | `KB881135::39187679::646dad6633ea4941043e205a01aa00e63f405610243a401dd7d7f1c362161f6f::0004` | `KB881135::39127058::f5959386c0f4d87ca9473dc8ab104739e42a3ed3b3b05d60127d78f3d81a6674::0004` | False |
| 4 | `KB875759::39002995::782dd1bd928ad04b242485cc9d6bb0a305bb199e62bd42a09aaa0c70880ec68b::0006` | `KB875759::38794940::5778c1098db572c3169b864f63675e17c5f1d68142e224502e279d4484e0203d::0004` | False |
| 5 | `KB881136::39007114::c7e0e1085aae05331b447fe98e78216a48f3909404c93d02d0ea56d7ea5e99ee::0006` | `KB881136::38966530::49006a8f0a51e0da7b55fb68fe1de172597f0ec356b7cfcf0d5dc8da1522337e::0005` | False |

### tfidf_v1: `rates_billing_usage__9ada4c1a54049658__87ccc0ff65e71b1e.query_context.json`

- Returned: 5
- Candidate chunks: 504
- Post-diversity scored chunks: 83

| Rank | Score | KB | Bug / Patch | Product | Category | Matched Terms | Contributions |
|---:|---:|---|---|---|---|---|---|
| 1 | 68.70211 | KB881135 | 39109281 | Oracle Utilities Service and Measurement Data Foundation | Usage Rules | usage | usage:68.70211 |
| 2 | 65.954026 | KB875759 | 38884483 | Oracle Utilities Service and Measurement Data Foundation | Usage Rules | usage | usage:65.954026 |
| 3 | 65.954026 | KB881135 | 39187679 | Oracle Utilities Service and Measurement Data Foundation | Usage | usage | usage:65.954026 |
| 4 | 61.145076 | KB875759 | 39002995 | Oracle Utilities Service and Measurement Data Foundation | Usage | rates, usage | rates:8.931472, usage:52.213604 |
| 5 | 61.145076 | KB881136 | 39007114 | Oracle Utilities Service and Measurement Data Foundation | Usage | rates, usage | rates:8.931472, usage:52.213604 |

### bm25_v1: `rates_billing_usage__9ada4c1a54049658__e07eeade1c9e0a16.query_context.json`

- Returned: 5
- Candidate chunks: 504
- Post-diversity scored chunks: 83
- BM25 k1: 1.2
- BM25 b: 0.75
- Average document length: 177.710615

| Rank | Score | KB | Bug / Patch | Product | Category | Matched Terms | Contributions |
|---:|---:|---|---|---|---|---|---|
| 1 | 8.97746 | KB875759 | 39002995 | Oracle Utilities Service and Measurement Data Foundation | Usage | billing, rates, usage | billing:1.321378, rates:4.404736, usage:3.251346 |
| 2 | 8.97746 | KB881136 | 39007114 | Oracle Utilities Service and Measurement Data Foundation | Usage | billing, rates, usage | billing:1.321378, rates:4.404736, usage:3.251346 |
| 3 | 8.016685 | KB881135 | 39127058 | Oracle Utilities Service and Measurement Data Foundation | Usage | rates, usage | rates:4.450069, usage:3.566616 |
| 4 | 7.735204 | KB875759 | 38794940 | Oracle Utilities Service and Measurement Data Foundation | Usage | rates, usage | rates:4.639323, usage:3.095881 |
| 5 | 6.779924 | KB881136 | 38966530 | Oracle Utilities Service and Measurement Data Foundation | Usage | rates, usage | rates:3.489463, usage:3.290461 |
