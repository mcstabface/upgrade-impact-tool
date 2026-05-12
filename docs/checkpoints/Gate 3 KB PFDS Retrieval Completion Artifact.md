# Gate 3 KB PFDS Retrieval Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: KB PFDS Retrieval Index and Query  
Status: Complete for current sample corpus  
Generated: 2026-05-12

## Purpose

This checkpoint captures the completed state of Gate 3 for the KB ingestion/customization phase.

Gate 3 answered this bounded question:

> Can the system build a deterministic retrieval index over Gate 2 PFDS chunks and return ranked source chunks with full KB/PFDS lineage?

For the current sample corpus, the answer is yes.

Gate 3 remains source retrieval only. It does not generate upgrade impact analysis, infer business truth, or call an LLM.

## Source Baseline

Gate 3 starts from Gate 2 search-context chunk artifacts.

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

Gate 3 indexes only the Gate 2 chunk collections.

## Gate 3 Pipeline

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate3_kb_retrieval
```

Dry run:

```bash
python -m app.scripts.run_gate3_kb_retrieval --dry-run
```

Custom smoke query:

```bash
python -m app.scripts.run_gate3_kb_retrieval --smoke-query "market transaction message error"
```

The orchestrator runs these modules in order:

1. `app.scripts.build_kb_chunk_lexical_index`
2. `app.scripts.query_kb_chunks`
3. `app.scripts.validate_gate3_kb_retrieval`
4. `app.scripts.write_kb_retrieval_summary`

## Generated Artifacts

| Artifact | Purpose |
|---|---|
| `kbs/indexes/kb_chunk_lexical_index.sqlite` | SQLite lexical index over Gate 2 chunk text and metadata |
| `kbs/manifests/kb_chunk_lexical_index_manifest.json` | Index build manifest with collection, chunk, posting, vocabulary, and failure counts |
| `kbs/query_context/*.query_context.json` | Query result artifacts with ranked chunks, scores, matched terms, and KB/PFDS lineage |
| `kbs/manifests/kb_retrieval_summary.md` | Reviewer-facing Gate 3 retrieval summary report |

Generated index/query artifacts are ignored by Git:

- `kbs/indexes/`
- `kbs/query_context/`

Manifests and summaries remain reviewable and may be committed intentionally.

## Latest Verified Pipeline Output

Local run completed successfully with:

```text
python -m app.scripts.run_gate3_kb_retrieval
```

Index build:

- Collections: 179
- Indexed collections: 179
- Chunks: 895
- Indexed chunks: 895
- Posting rows: 79,073
- Vocabulary size: 4,857
- Failures: 0

Smoke query:

```text
rates billing usage
```

Smoke query result:

- Query ID: `9ada4c1a54049658`
- Query terms: `rates`, `billing`, `usage`
- Candidate chunks: 504
- Returned chunks: 5
- Ranker: `term_frequency_idf_v1`

Validation:

```text
[gate3:validate] OK
```

## Validation Invariants

Gate 3 validates these invariants:

```text
collection_count == Gate 2 chunk_collection_count
179 == 179
```

```text
indexed_collection_count == Gate 2 chunk_collection_count
179 == 179
```

```text
chunk_count == Gate 2 chunk_count
895 == 895
```

```text
indexed_chunk_count == Gate 2 chunk_count
895 == 895
```

```text
posting_count > 0
79073 > 0
```

```text
vocabulary_size > 0
4857 > 0
```

The validator also checks that the SQLite index contains the required tables:

- `metadata`
- `chunks`
- `postings`

and that SQLite row counts match the manifest counts.

## Per-KB Index Breakdown

| KB | Collections | Indexed Chunks | Tokens |
|---|---:|---:|---:|
| KB869018 | 34 | 164 | 29,671 |
| KB875759 | 56 | 306 | 55,296 |
| KB881135 | 35 | 179 | 31,166 |
| KB881136 | 54 | 246 | 42,918 |

## Product Breakdown

| Product | Collections | Indexed Chunks |
|---|---:|---:|
| Oracle Utilities Framework | 55 | 158 |
| Oracle Utilities Customer Care and Billing | 53 | 390 |
| Oracle Utilities Service and Measurement Data Foundation | 47 | 244 |
| Oracle Utilities Customer to Meter | 18 | 77 |
| Oracle Utilities Cloud Service Foundation | 4 | 17 |
| Oracle Utilities Asset Management Base | 2 | 9 |

## Smoke Query Top Results

Query:

```text
rates billing usage
```

Top 5 returned chunks:

| Rank | Score | KB | Bug / Patch | Product | Category | Matched Terms |
|---:|---:|---|---|---|---|---|
| 1 | 68.70211 | KB881135 | 39109281 | Oracle Utilities Service and Measurement Data Foundation | Usage Rules | usage |
| 2 | 65.954026 | KB875759 | 38884483 | Oracle Utilities Service and Measurement Data Foundation | Usage Rules | usage |
| 3 | 65.954026 | KB881135 | 39187679 | Oracle Utilities Service and Measurement Data Foundation | Usage | usage |
| 4 | 63.205941 | KB875759 | 38884483 | Oracle Utilities Service and Measurement Data Foundation | Usage Rules | usage |
| 5 | 61.145076 | KB875759 | 39002995 | Oracle Utilities Service and Measurement Data Foundation | Usage | rates, usage |

This proves the query path can return ranked PFDS chunks with KB, MP, bug/patch, product, category, and child-PDF lineage.

## Key Code Added During Gate 3

| Script | Purpose |
|---|---|
| `backend/app/scripts/build_kb_chunk_lexical_index.py` | Build SQLite lexical index over Gate 2 KB PFDS chunks |
| `backend/app/scripts/query_kb_chunks.py` | Query SQLite lexical index and write query-context artifacts |
| `backend/app/scripts/validate_gate3_kb_retrieval.py` | Validate manifest and SQLite index invariants |
| `backend/app/scripts/write_kb_retrieval_summary.py` | Produce reviewer-facing Markdown retrieval summary |
| `backend/app/scripts/run_gate3_kb_retrieval.py` | Run Gate 3 end-to-end |

## SQLite Index Contract

The SQLite index contains:

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

## Query Context Contract

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

This is intentionally simple and deterministic. It is not final relevance engineering.

## What This Proves

Gate 3 proves that the project can now:

- consume Gate 2 chunk manifests as source truth,
- build a local deterministic SQLite lexical index,
- preserve PFDS lineage in the index,
- return ranked source chunks for a query,
- emit query-context artifacts,
- validate index and query artifacts,
- produce a reviewer-facing retrieval summary.

## Known Limitations

Gate 3 remains deliberately lexical and deterministic.

Known limitations:

- It does not use embeddings.
- It does not use BM25 yet.
- It does not apply phrase/proximity scoring.
- It does not support product/category/KB filters yet.
- It does not deduplicate multiple chunks from the same PFDS file.
- It does not diversify results by source document.
- It does not summarize results.
- It does not generate upgrade impact analysis.
- It does not expose retrieval in the web UI yet.
- It assumes Gate 2 generated chunk artifacts are available locally.

These limitations are acceptable for Gate 3. They define the next gate.

## Important Finding

The default smoke query `rates billing usage` returned mostly Usage/Usage Rules records because `usage` had strong term frequency and IDF behavior in the current corpus.

This is not a bug. It is useful baseline evidence that lexical ranking works, but also proves the next gate should improve diagnostics and ranking controls before any impact-generation layer is added.

## Recommended Next Gate

Recommended next gate:

**Gate 4 — Retrieval Quality Diagnostics and Controls**

Gate 4 should improve search quality and observability while staying deterministic.

Proposed Gate 4 sequence:

1. Add richer query diagnostics:
   - per-term document frequency
   - per-term contribution to score
   - candidate count by term
   - why each top result matched
2. Add optional query filters:
   - KB document ID
   - maintenance pack
   - product
   - category
   - bug / patch number
3. Add source diversity controls:
   - max chunks per child PDF
   - max chunks per bug/patch
4. Add phrase/proximity scoring bonus.
5. Add BM25 as an alternate deterministic ranker.
6. Add retrieval evaluation fixture with expected result assertions.
7. Only after quality diagnostics are useful, consider embeddings or hybrid retrieval.

Do not start with impact generation. The next step is explainable, controllable retrieval quality.

## Recommended Next Chat Starting Point

Use this prompt to continue in a new chat:

```text
We are continuing work on the Upgrade Impact Analysis Tool.

Gate 1 completed KB source extraction and PFDS evidence mapping.
Gate 2 completed KB PFDS source text extraction and deterministic chunking.
Gate 3 completed KB PFDS lexical retrieval index and query.

Use this repo as source of truth:
mcstabface/upgrade-impact-tool

Start from these docs/artifacts:
- docs/checkpoints/Gate 1 KB Source Extraction Completion Artifact.md
- docs/checkpoints/Gate 2 KB Search Context Completion Artifact.md
- docs/checkpoints/Gate 3 KB PFDS Retrieval Completion Artifact.md
- kbs/manifests/kb_search_context_summary.md
- kbs/manifests/kb_search_context_chunks_manifest.json
- kbs/manifests/kb_chunk_lexical_index_manifest.json
- kbs/manifests/kb_retrieval_summary.md
- backend/app/scripts/run_gate3_kb_retrieval.py

Current Gate 3 status:
- 179 indexed PFDS chunk collections
- 895 indexed PFDS chunks
- 79,073 posting rows
- 4,857 vocabulary terms
- 0 index failures
- smoke query returned 5 ranked chunks
- validator passes with `[gate3:validate] OK`

The Gate 3 pipeline runs successfully with:
python -m app.scripts.run_gate3_kb_retrieval

Next recommended gate is Gate 4: Retrieval Quality Diagnostics and Controls.

Please review the repo and produce the next concrete build plan and first patches for Gate 4.
Be specific, repo-grounded, and provide exact patch contents.
```

## Completion Status

Gate 3 is complete for the current source corpus.

The next work should begin from this checkpoint, not from memory.
