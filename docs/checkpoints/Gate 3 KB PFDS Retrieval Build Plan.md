# Gate 3 KB PFDS Retrieval Build Plan

System: Upgrade Impact Analysis Tool  
Phase: KB PFDS Retrieval Index and Query  
Status: Initial lexical retrieval slice  
Generated: 2026-05-12

## Starting Point

Gate 1 completed KB source extraction and PFDS evidence mapping.

Gate 2 completed matched PFDS source text extraction and deterministic chunking.

Current Gate 2 baseline:

- 179 matched PFDS evidence rows
- 179 search-context artifacts
- 0 text extraction failures
- 0 empty-text artifacts
- 178 image-bearing artifacts
- 0 highlight-bearing artifacts
- 179 chunk collections
- 895 chunks
- 0 chunking skips
- 0 chunking failures

Gate 3 starts from:

```text
kbs/manifests/kb_search_context_chunks_manifest.json
kbs/search_context_chunks/
```

## Gate 3 Objective

Gate 3 answers this bounded question:

> Can the system build a deterministic retrieval index over Gate 2 PFDS chunks and return ranked source chunks with full KB/PFDS lineage?

This gate does not generate upgrade impact analysis.

The first slice is lexical only. Embeddings and hybrid retrieval are intentionally deferred until deterministic lexical retrieval is working and inspectable.

## First Implementation Slice

Added scripts:

| Script | Purpose |
|---|---|
| `backend/app/scripts/build_kb_chunk_lexical_index.py` | Builds a deterministic SQLite lexical index over Gate 2 chunk collection artifacts. |
| `backend/app/scripts/query_kb_chunks.py` | Queries the SQLite lexical index and writes query-context artifacts with ranked chunks and source lineage. |
| `backend/app/scripts/run_gate3_kb_retrieval.py` | Runs the Gate 3 index build and a smoke query. |

Generated outputs:

| Artifact | Purpose |
|---|---|
| `kbs/indexes/kb_chunk_lexical_index.sqlite` | SQLite lexical index over chunk text and metadata. |
| `kbs/manifests/kb_chunk_lexical_index_manifest.json` | Index build manifest with collection, chunk, posting, vocabulary, and failure counts. |
| `kbs/query_context/*.query_context.json` | Query result artifacts with ranked chunks, scores, matched terms, and KB/PFDS lineage. |

Generated index/query artifacts are ignored by Git unless intentionally added.

## Run Commands

From backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate3_kb_retrieval
```

Dry run:

```bash
python -m app.scripts.run_gate3_kb_retrieval --dry-run
```

Build index directly:

```bash
python -m app.scripts.build_kb_chunk_lexical_index
```

Query directly:

```bash
python -m app.scripts.query_kb_chunks "rates billing usage" --top-k 5
```

Run a different smoke query:

```bash
python -m app.scripts.run_gate3_kb_retrieval --smoke-query "market transaction message error"
```

## SQLite Index Schema

The index contains:

```text
metadata(key, value)
chunks(chunk_id, lineage fields, text, offsets, token_count, text_sha256)
postings(term, chunk_id, term_count)
```

Lineage preserved in `chunks`:

- KB document ID
- maintenance pack
- bug / patch number
- product
- category
- portfolio file
- child PDF path
- child SHA-256
- collection path
- source artifact path
- chunk index
- character offsets

## Ranking Model

Initial ranker:

```text
term_frequency_idf_v1
```

Score calculation:

```text
sum(query_term_count * chunk_term_count * idf)
```

where:

```text
idf = log((1 + total_chunks) / (1 + document_frequency)) + 1
```

Sort order:

```text
score descending, chunk_id ascending
```

This is intentionally simple and deterministic. It is a baseline retrieval stage, not final relevance engineering.

## Query Context Artifact Contract

Each query writes:

```text
artifact_type = kb_chunk_query_context
schema_version = kb_chunk_query_context.v1
```

It includes:

- query ID
- query text
- normalized query terms
- index metadata
- diagnostics
- ranked results
- matched terms
- term hits
- scores
- full chunk text
- KB/PFDS lineage

## Acceptance Criteria

Gate 3 initial lexical retrieval is complete when:

1. `python -m app.scripts.run_gate3_kb_retrieval` completes successfully.
2. `kbs/indexes/kb_chunk_lexical_index.sqlite` exists.
3. `kbs/manifests/kb_chunk_lexical_index_manifest.json` exists.
4. Index manifest `indexed_collection_count` equals Gate 2 `chunk_collection_count` for the same corpus.
5. Index manifest `indexed_chunk_count` equals Gate 2 `chunk_count` for the same corpus.
6. Index manifest `posting_count` is greater than zero.
7. Query script returns ranked chunks with KB/PFDS lineage.
8. Query script writes a `kb_chunk_query_context` artifact unless `--no-write` is passed.

Expected current corpus values:

```text
indexed_collection_count = 179
indexed_chunk_count = 895
```

## Non-Goals

Gate 3 initial slice does not:

- call an LLM,
- generate upgrade impact analysis,
- generate summaries,
- build embeddings,
- build a vector index,
- perform OCR or image understanding,
- resolve Gate 1 missing evidence exceptions.

## Next Build Steps

### Step 1 — Run Gate 3 locally

```bash
python -m app.scripts.run_gate3_kb_retrieval
```

Review:

```text
kbs/manifests/kb_chunk_lexical_index_manifest.json
kbs/query_context/*.query_context.json
```

### Step 2 — Add Gate 3 validation

Add:

```text
backend/app/scripts/validate_gate3_kb_retrieval.py
```

It should verify:

- index DB exists,
- required tables exist,
- indexed collection count matches Gate 2,
- indexed chunk count matches Gate 2,
- posting count > 0,
- smoke query artifact exists and returned at least one result.

### Step 3 — Add query summary report

Add:

```text
backend/app/scripts/write_kb_retrieval_summary.py
```

Summarize:

- indexed collections,
- indexed chunks,
- vocabulary size,
- posting count,
- smoke query,
- returned chunks,
- top result lineage.

### Step 4 — Retrieval quality tuning

After the baseline works, improve ranking with deterministic techniques:

- phrase proximity bonus,
- product/category filters,
- bug/patch exact-match handling,
- source diversity cap,
- query diagnostics expansion.

Embeddings remain later.
