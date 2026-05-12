# Gate 4 KB Retrieval Diagnostics Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Retrieval Quality Diagnostics and Controls  
Status: Initial diagnostics/control slice  
Generated: 2026-05-12

## Starting Point

Gate 1 completed KB source extraction and PFDS evidence mapping.

Gate 2 completed matched PFDS source text extraction and deterministic chunking.

Gate 3 completed deterministic lexical retrieval over PFDS chunks.

Current Gate 3 baseline:

- 179 indexed PFDS chunk collections
- 895 indexed PFDS chunks
- 79,073 posting rows
- 4,857 vocabulary terms
- 0 index failures
- smoke query returned 5 ranked chunks
- validator passes with `[gate3:validate] OK`

## Gate 4 Objective

Gate 4 answers this bounded question:

> Can the retrieval layer explain and control why PFDS chunks are returned before any upgrade-impact generation is attempted?

The first slice adds diagnostics and controls to the existing deterministic lexical retriever.

This gate does not:

- call an LLM,
- generate upgrade impact analysis,
- build embeddings,
- introduce semantic retrieval,
- change Gate 1/2/3 artifact contracts beyond query context schema evolution.

## First Implementation Slice

Updated:

| File | Purpose |
|---|---|
| `backend/app/scripts/query_kb_chunks.py` | Adds v2 query context diagnostics, optional query filters, score contribution details, and source diversity controls. |
| `backend/app/scripts/run_gate4_kb_retrieval_diagnostics.py` | Runs index build plus diagnostic smoke queries. |

## Query Context v2 Additions

`query_kb_chunks.py` now emits:

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

New per-result fields:

- `term_score_contributions`

## Term Diagnostics

For each query term, diagnostics include:

- global posting count
- filtered posting count
- IDF value
- candidate limit
- whether candidate retrieval was limited

This makes ranking behavior explainable without reading SQLite manually.

## Query Filters

Supported filters:

```text
--kb-document-id
--maintenance-pack
--bug-patch-number
--product
--category
```

Example:

```bash
python -m app.scripts.query_kb_chunks "rates billing usage" \
  --product "Oracle Utilities Customer Care and Billing" \
  --top-k 5
```

Filters are applied at candidate retrieval time, not after ranking.

## Source Diversity Controls

Supported controls:

```text
--max-chunks-per-child-pdf
--max-chunks-per-bug-patch
```

Example:

```bash
python -m app.scripts.query_kb_chunks "rates billing usage" \
  --top-k 5 \
  --max-chunks-per-child-pdf 1 \
  --max-chunks-per-bug-patch 1
```

These controls reduce repeated chunks from the same child PDF or bug/patch in the ranked result set.

## Gate 4 Runner

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

The runner executes:

1. `app.scripts.build_kb_chunk_lexical_index`
2. unfiltered diagnostic smoke query with source diversity controls
3. filtered diagnostic smoke query
4. `app.scripts.validate_gate3_kb_retrieval`
5. `app.scripts.write_kb_retrieval_summary`

## Acceptance Criteria

Gate 4 initial slice is complete when:

1. `python -m app.scripts.run_gate4_kb_retrieval_diagnostics` completes successfully.
2. Query context artifacts use `schema_version = kb_chunk_query_context.v2`.
3. Query context diagnostics include `term_diagnostics`.
4. Each returned result includes `term_score_contributions`.
5. A filtered query returns only results matching the requested filter.
6. Source diversity controls report exclusions under `diagnostics.source_diversity.excluded_by_reason` when applicable.
7. Gate 3 validator still passes.

## Suggested Local Verification

Run:

```bash
python -m app.scripts.run_gate4_kb_retrieval_diagnostics
```

Then inspect latest query context:

```bash
python - <<'PY'
import json
from pathlib import Path
root = Path('../kbs/query_context')
latest = max(root.glob('*.query_context.json'), key=lambda p: p.stat().st_mtime)
q = json.loads(latest.read_text())
print(latest)
print(q['schema_version'])
print(q['query']['filters'])
print(q['diagnostics']['term_diagnostics'])
print(q['diagnostics']['source_diversity'])
print(q['results'][0]['term_score_contributions'] if q['results'] else 'NO RESULTS')
PY
```

## Next Build Steps

### Step 1 — Add Gate 4 validator

Add:

```text
backend/app/scripts/validate_gate4_kb_retrieval_diagnostics.py
```

It should verify:

- latest query contexts are v2,
- term diagnostics exist,
- result score contributions exist,
- filtered query result lineage matches the filter,
- diversity diagnostics exist.

### Step 2 — Update retrieval summary

Update `write_kb_retrieval_summary.py` to display:

- term diagnostics table,
- source diversity exclusions,
- active filters,
- score contribution summaries.

### Step 3 — Add BM25 alternate ranker

After diagnostics are stable, add deterministic BM25 as an alternate ranker. Do not add embeddings first.

### Step 4 — Add evaluation fixture

Add a small, deterministic retrieval evaluation file with expected lineage assertions for 3–5 queries.

## Non-Goals

Gate 4 initial slice does not:

- generate upgrade impact analysis,
- generate summaries,
- call an LLM,
- build embeddings,
- change Gate 1/2/3 source artifacts,
- introduce web UI behavior.

## Notes

This gate turns retrieval from “it returned something” into “we can explain why it returned this and constrain what it is allowed to return.”

That distinction matters before any downstream analysis relies on retrieved PFDS evidence.
