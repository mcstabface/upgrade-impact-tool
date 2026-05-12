# Gate 4 KB Retrieval Diagnostics Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: Retrieval Quality Diagnostics and Controls  
Status: Complete for current sample corpus  
Generated: 2026-05-12

## Purpose

This checkpoint captures the completed state of Gate 4 for the KB ingestion/customization phase.

Gate 4 answered this bounded question:

> Can the retrieval layer explain and control why PFDS chunks are returned before any upgrade-impact generation is attempted?

For the current sample corpus, the answer is yes.

Gate 4 remains deterministic retrieval diagnostics only. It does not generate upgrade impact analysis, infer business truth, call an LLM, or use embeddings.

## Source Baseline

Gate 4 starts from Gate 3 lexical retrieval.

Current Gate 3 baseline:

- 179 indexed PFDS chunk collections
- 895 indexed PFDS chunks
- 79,073 posting rows
- 4,857 vocabulary terms
- 0 index failures
- validator passes with `[gate3:validate] OK`

## Gate 4 Pipeline

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate4_kb_retrieval_diagnostics
```

Dry run:

```bash
python -m app.scripts.run_gate4_kb_retrieval_diagnostics --dry-run
```

The orchestrator runs these modules in order:

1. `app.scripts.build_kb_chunk_lexical_index`
2. `app.scripts.query_kb_chunks` with source-diversity controls
3. `app.scripts.query_kb_chunks` with product filter and source-diversity controls
4. `app.scripts.validate_gate3_kb_retrieval`
5. `app.scripts.validate_gate4_kb_retrieval_diagnostics`
6. `app.scripts.write_kb_retrieval_summary`

## Generated Artifacts

| Artifact | Purpose |
|---|---|
| `kbs/indexes/kb_chunk_lexical_index.sqlite` | SQLite lexical index over Gate 2 chunk text and metadata |
| `kbs/manifests/kb_chunk_lexical_index_manifest.json` | Index build manifest with collection, chunk, posting, vocabulary, and failure counts |
| `kbs/query_context/*.query_context.json` | Query result artifacts with ranked chunks, scores, matched terms, diagnostics, and KB/PFDS lineage |
| `kbs/manifests/kb_retrieval_summary.md` | Reviewer-facing retrieval summary report with Gate 4 diagnostics |

Generated index/query artifacts are ignored by Git:

- `kbs/indexes/`
- `kbs/query_context/`

Manifests and summaries remain reviewable and may be committed intentionally.

## Latest Verified Pipeline Output

Local clean run completed successfully with:

```text
python -m app.scripts.run_gate4_kb_retrieval_diagnostics
```

Index build:

- Collections: 179
- Indexed collections: 179
- Chunks: 895
- Indexed chunks: 895
- Posting rows: 79,073
- Vocabulary size: 4,857
- Failures: 0

Validation:

```text
[gate3:validate] OK
[gate4:validate] OK
```

## Query Context v2 Contract

Gate 4 upgrades query contexts to:

```text
schema_version = kb_chunk_query_context.v2
```

New query fields:

- `filters`
- `max_chunks_per_child_pdf`
- `max_chunks_per_bug_patch`

New diagnostics fields:

- `term_diagnostics`
- `post_diversity_scored_count`
- `source_diversity`

New per-result field:

- `term_score_contributions`

## Query Artifact Identity Fix

During Gate 4 validation, a defect was found:

- both diagnostic queries used the same query text,
- query-context filenames were based only on query text,
- the second query overwrote the first,
- the validator then inspected an older v1 query-context artifact.

Fix:

Query-context artifact identity now includes:

- query text
- filters
- top-k
- candidate limit
- source diversity controls
- ranker
- schema version

New filename pattern:

```text
{query_slug}__{query_id}__{context_id}.query_context.json
```

This makes query artifacts deterministic without collapsing distinct retrieval-control configurations.

## Latest Diagnostic Query Results

Latest filtered smoke query:

```text
rates billing usage
```

Active filter:

```json
{"product": "Oracle Utilities Customer Care and Billing"}
```

Diagnostics:

- Candidate chunks: 373
- Scored chunks: 373
- Post-diversity scored chunks: 53
- Returned chunks: 5
- Ranker: `term_frequency_idf_v1`

Term diagnostics:

| Term | Global Postings | Filtered Postings | IDF | Candidate Limited |
|---|---:|---:|---:|---|
| billing | 393 | 371 | 1.82159 | False |
| rates | 27 | 0 | 4.465736 | False |
| usage | 155 | 31 | 2.748084 | False |

Source diversity controls:

- Enabled: True
- Max chunks per child PDF: 1
- Max chunks per bug / patch: None
- Excluded by `max_chunks_per_child_pdf`: 320

Top 5 returned chunks:

| Rank | Score | KB | Bug / Patch | Product | Category | Matched Terms | Score Contributions |
|---:|---:|---|---|---|---|---|---|
| 1 | 42.116361 | KB881135 | 39064768 | Oracle Utilities Customer Care and Billing | Conversion | billing, usage | billing:3.643179, usage:38.473182 |
| 2 | 31.124023 | KB881135 | 39234264 | Oracle Utilities Customer Care and Billing | Billing | billing, usage | billing:3.643179, usage:27.480844 |
| 3 | 29.271033 | KB869018 | 38848234 | Oracle Utilities Customer Care and Billing | Billing | billing, usage | billing:7.286358, usage:21.984675 |
| 4 | 22.87977 | KB881135 | 38959224 | Oracle Utilities Customer Care and Billing | Case Management | billing, usage | billing:3.643179, usage:19.236591 |
| 5 | 21.05818 | KB881136 | 38959233 | Oracle Utilities Customer Care and Billing | Case Management | billing, usage | billing:1.82159, usage:19.236591 |

## Recent Query Context Artifacts

The latest summary confirms the two newest Gate 4 query contexts are distinct v2 artifacts:

| Artifact | Schema | Query | Filters | Returned | Diversity Enabled |
|---|---|---|---|---:|---|
| `rates_billing_usage__9ada4c1a54049658__e2c0da700deed94f.query_context.json` | `kb_chunk_query_context.v2` | `rates billing usage` | product filter | 5 | True |
| `rates_billing_usage__9ada4c1a54049658__9253a81d8c710522.query_context.json` | `kb_chunk_query_context.v2` | `rates billing usage` | none | 5 | True |

## Key Code Added or Updated During Gate 4

| Script | Purpose |
|---|---|
| `backend/app/scripts/query_kb_chunks.py` | Adds v2 diagnostics, query filters, score contributions, source diversity controls, and context-aware artifact identity |
| `backend/app/scripts/run_gate4_kb_retrieval_diagnostics.py` | Runs Gate 4 diagnostic retrieval smoke checks end-to-end |
| `backend/app/scripts/validate_gate4_kb_retrieval_diagnostics.py` | Validates v2 query diagnostics, filters, and source diversity controls |
| `backend/app/scripts/write_kb_retrieval_summary.py` | Surfaces Gate 4 diagnostics in Markdown summary |

## Validation Coverage

Gate 4 validator checks:

- newest query contexts use `kb_chunk_query_context.v2`,
- query contexts contain non-empty term diagnostics,
- query contexts contain source-diversity diagnostics,
- returned results contain term score contributions,
- filtered query results match active filters,
- at least one recent query context includes filters,
- at least one recent query context has source diversity enabled.

Gate 3 validator still checks index integrity:

- collection/chunk counts match Gate 2,
- posting count is greater than zero,
- vocabulary size is greater than zero,
- SQLite tables exist,
- SQLite row counts match manifest counts.

## What This Proves

Gate 4 proves that the project can now:

- explain why query terms matched,
- show global and filtered posting counts per term,
- show IDF values per term,
- show per-result term score contributions,
- constrain retrieval by lineage fields,
- reduce repeated chunks from the same source PDF or bug/patch,
- validate query-context diagnostics,
- render retrieval diagnostics for human review.

## Known Limitations

Gate 4 remains lexical and deterministic.

Known limitations:

- It does not use BM25 yet.
- It does not use embeddings.
- It does not use phrase/proximity scoring.
- It does not include a query evaluation fixture yet.
- It does not summarize retrieved evidence.
- It does not generate upgrade impact analysis.
- It does not expose retrieval in the web UI yet.
- Query diagnostics are still CLI/artifact-oriented, not interactive.

These limitations are acceptable for Gate 4. They define the next gate.

## Important Finding

The product-filtered query showed that the term `rates` had zero filtered postings for `Oracle Utilities Customer Care and Billing` even though it had 27 global postings.

That is exactly the kind of retrieval behavior Gate 4 needed to expose. Without term diagnostics, this would look like a relevance mystery. With diagnostics, it is visible and explainable.

## Recommended Next Gate

Recommended next gate:

**Gate 5 — Deterministic BM25 Ranking and Retrieval Evaluation**

Gate 5 should improve ranking quality while preserving deterministic, explainable retrieval.

Proposed Gate 5 sequence:

1. Add BM25 as an alternate ranker:
   - `--ranker tfidf`
   - `--ranker bm25`
2. Add BM25 diagnostics:
   - average document length
   - per-term BM25 contribution
   - k1/b parameters
3. Add retrieval evaluation fixture:
   - small query set,
   - expected KB/product/category/bug assertions,
   - pass/fail summary.
4. Add comparison report:
   - TF-IDF top results,
   - BM25 top results,
   - evaluation score deltas.
5. Only after lexical ranking quality is measurable, consider embeddings or hybrid retrieval.

Do not start with impact generation. Retrieval quality still needs measurable ranking baselines.

## Recommended Next Chat Starting Point

Use this prompt to continue in a new chat:

```text
We are continuing work on the Upgrade Impact Analysis Tool.

Gate 1 completed KB source extraction and PFDS evidence mapping.
Gate 2 completed KB PFDS source text extraction and deterministic chunking.
Gate 3 completed KB PFDS lexical retrieval index and query.
Gate 4 completed retrieval diagnostics and controls.

Use this repo as source of truth:
mcstabface/upgrade-impact-tool

Start from these docs/artifacts:
- docs/checkpoints/Gate 1 KB Source Extraction Completion Artifact.md
- docs/checkpoints/Gate 2 KB Search Context Completion Artifact.md
- docs/checkpoints/Gate 3 KB PFDS Retrieval Completion Artifact.md
- docs/checkpoints/Gate 4 KB Retrieval Diagnostics Completion Artifact.md
- kbs/manifests/kb_retrieval_summary.md
- backend/app/scripts/query_kb_chunks.py
- backend/app/scripts/run_gate4_kb_retrieval_diagnostics.py
- backend/app/scripts/validate_gate4_kb_retrieval_diagnostics.py

Current Gate 4 status:
- 179 indexed PFDS chunk collections
- 895 indexed PFDS chunks
- 79,073 posting rows
- 4,857 vocabulary terms
- query contexts use `kb_chunk_query_context.v2`
- term diagnostics are emitted
- source diversity controls are emitted
- filtered query results are validated against active filters
- summary reports active filters, term diagnostics, source diversity exclusions, and score contributions
- validator passes with `[gate4:validate] OK`

The Gate 4 pipeline runs successfully with:
python -m app.scripts.run_gate4_kb_retrieval_diagnostics

Next recommended gate is Gate 5: Deterministic BM25 Ranking and Retrieval Evaluation.

Please review the repo and produce the next concrete build plan and first patches for Gate 5.
Be specific, repo-grounded, and provide exact patch contents.
```

## Completion Status

Gate 4 is complete for the current source corpus.

The next work should begin from this checkpoint, not from memory.
