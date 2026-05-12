# Gate 5 BM25 Ranking Evaluation Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Deterministic BM25 Ranking and Retrieval Evaluation  
Status: Initial BM25 ranking slice  
Generated: 2026-05-12

## Starting Point

Gate 1 completed KB source extraction and PFDS evidence mapping.

Gate 2 completed matched PFDS source text extraction and deterministic chunking.

Gate 3 completed deterministic lexical retrieval over PFDS chunks.

Gate 4 completed retrieval diagnostics and controls.

Current Gate 4 baseline:

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

## Gate 5 Objective

Gate 5 answers this bounded question:

> Can the retrieval layer compare deterministic ranking strategies and begin measuring retrieval quality before downstream impact generation begins?

The first Gate 5 slice adds BM25 as an alternate deterministic ranker while preserving the existing TF-IDF ranker.

This gate does not:

- call an LLM,
- generate upgrade impact analysis,
- build embeddings,
- introduce semantic retrieval,
- change Gate 1/2 source artifacts.

## First Implementation Slice

Updated:

| File | Purpose |
|---|---|
| `backend/app/scripts/query_kb_chunks.py` | Adds `--ranker tfidf` and `--ranker bm25`, BM25 k1/b parameters, BM25 diagnostics, and per-term BM25 score contributions. |
| `backend/app/scripts/run_gate5_kb_bm25_eval.py` | Runs TF-IDF and BM25 comparisons for unfiltered and filtered diagnostic queries. |

## Ranker Options

Supported rankers:

```text
--ranker tfidf
--ranker bm25
```

Default:

```text
--ranker tfidf
```

This preserves Gate 3/4 behavior.

## BM25 Parameters

Defaults:

```text
--bm25-k1 1.2
--bm25-b 0.75
```

BM25 diagnostics include:

- ranker name: `bm25_v1`
- k1
- b
- average document length
- document length field: `chunks.token_count`
- per-term BM25 contribution
- BM25 IDF per query term

## Query Context Contract

Gate 5 still emits:

```text
schema_version = kb_chunk_query_context.v2
```

No schema-version bump is required because the existing v2 diagnostics shape already supports ranker-specific diagnostics and per-term score contributions.

New/expanded fields:

```text
query.ranker
query.bm25_k1
query.bm25_b
diagnostics.ranker
diagnostics.ranker_diagnostics
term_diagnostics[*].bm25_idf
term_diagnostics[*].tfidf_idf
results[*].term_score_contributions
```

## Gate 5 Runner

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate5_kb_bm25_eval
```

Dry run:

```bash
python -m app.scripts.run_gate5_kb_bm25_eval --dry-run
```

Custom query:

```bash
python -m app.scripts.run_gate5_kb_bm25_eval --query "rates billing usage"
```

The runner executes:

1. `app.scripts.build_kb_chunk_lexical_index`
2. TF-IDF unfiltered comparison query
3. BM25 unfiltered comparison query
4. TF-IDF filtered comparison query
5. BM25 filtered comparison query
6. `app.scripts.validate_gate3_kb_retrieval`
7. `app.scripts.validate_gate4_kb_retrieval_diagnostics`
8. `app.scripts.write_kb_retrieval_summary`

## Acceptance Criteria

Gate 5 initial BM25 slice is complete when:

1. `python -m app.scripts.run_gate5_kb_bm25_eval` completes successfully.
2. TF-IDF query contexts are emitted with `diagnostics.ranker = tfidf_v1`.
3. BM25 query contexts are emitted with `diagnostics.ranker = bm25_v1`.
4. BM25 contexts include `diagnostics.ranker_diagnostics.average_document_length`.
5. BM25 contexts include k1 and b parameter values.
6. BM25 returned results include `term_score_contributions`.
7. Gate 3 validator still passes.
8. Gate 4 validator still passes.

## Suggested Local Verification

Run:

```bash
python -m app.scripts.run_gate5_kb_bm25_eval
```

Then inspect recent query contexts:

```bash
python - <<'PY'
import json
from pathlib import Path
root = Path('../kbs/query_context')
for path in sorted(root.glob('*.query_context.json'), key=lambda p: p.stat().st_mtime, reverse=True)[:6]:
    q = json.loads(path.read_text())
    print(path.name)
    print('  schema:', q['schema_version'])
    print('  ranker:', q['diagnostics']['ranker'])
    print('  filters:', q['query']['filters'])
    print('  returned:', q['diagnostics']['returned_count'])
    print('  ranker diagnostics:', q['diagnostics'].get('ranker_diagnostics'))
    print('  first result:', q['results'][0]['chunk_id'] if q['results'] else 'NO RESULTS')
PY
```

## Next Build Steps

### Step 1 — Add Gate 5 validator

Add:

```text
backend/app/scripts/validate_gate5_kb_bm25_eval.py
```

It should verify:

- newest query contexts include at least one TF-IDF and one BM25 context,
- BM25 diagnostics include average document length, k1, and b,
- result score contributions are present,
- filtered results still satisfy active filters.

### Step 2 — Add comparison summary

Update or add a report that compares:

- TF-IDF top results,
- BM25 top results,
- shared top chunks,
- changed ranking order,
- top result lineage per ranker.

Candidate file:

```text
backend/app/scripts/write_kb_bm25_comparison_summary.py
```

Output:

```text
kbs/manifests/kb_bm25_comparison_summary.md
```

### Step 3 — Add retrieval evaluation fixture

Add:

```text
kbs/eval/kb_retrieval_eval_set.json
backend/app/scripts/evaluate_kb_retrieval.py
```

The fixture should start small: 3–5 queries with expected KB/product/category/bug assertions.

### Step 4 — Gate 5 completion artifact

After evaluation exists and passes, add:

```text
docs/checkpoints/Gate 5 BM25 Ranking Evaluation Completion Artifact.md
```

## Non-Goals

Gate 5 initial slice does not:

- generate upgrade impact analysis,
- call an LLM,
- use embeddings,
- run OCR,
- expose retrieval in the web UI.

## Notes

BM25 is not automatically “better.” It is an alternate deterministic ranking strategy. Gate 5 exists to make ranking differences measurable before retrieval becomes an input to impact analysis.
