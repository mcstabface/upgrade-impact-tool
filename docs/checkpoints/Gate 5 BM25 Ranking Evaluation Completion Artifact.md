# Gate 5 BM25 Ranking Evaluation Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: Deterministic BM25 Ranking and Retrieval Evaluation  
Status: Complete for current sample corpus  
Generated: 2026-05-12

## Purpose

This checkpoint captures the completed state of Gate 5 for the KB ingestion/customization phase.

Gate 5 answered this bounded question:

> Can the retrieval layer compare deterministic ranking strategies and begin measuring retrieval quality before downstream impact generation begins?

For the current sample corpus, the answer is yes.

Gate 5 remains deterministic retrieval evaluation only. It does not generate upgrade impact analysis, infer business truth, call an LLM, use embeddings, or summarize retrieved evidence as impact.

## Source Baseline

Gate 5 starts from Gate 4 retrieval diagnostics and controls.

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

## Gate 5 Pipeline

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

Custom comparison query:

```bash
python -m app.scripts.run_gate5_kb_bm25_eval --query "rates billing usage"
```

The orchestrator runs these modules in order:

1. `app.scripts.build_kb_chunk_lexical_index`
2. `app.scripts.query_kb_chunks --ranker tfidf`
3. `app.scripts.query_kb_chunks --ranker bm25`
4. `app.scripts.query_kb_chunks --ranker tfidf --product ...`
5. `app.scripts.query_kb_chunks --ranker bm25 --product ...`
6. `app.scripts.validate_gate3_kb_retrieval`
7. `app.scripts.validate_gate4_kb_retrieval_diagnostics`
8. `app.scripts.validate_gate5_kb_bm25_eval`
9. `app.scripts.write_kb_retrieval_summary`
10. `app.scripts.write_kb_bm25_comparison_summary`
11. `app.scripts.evaluate_kb_retrieval`

## Generated Artifacts

| Artifact | Purpose |
|---|---|
| `kbs/indexes/kb_chunk_lexical_index.sqlite` | SQLite lexical index over Gate 2 chunk text and metadata |
| `kbs/manifests/kb_chunk_lexical_index_manifest.json` | Index build manifest with collection, chunk, posting, vocabulary, and failure counts |
| `kbs/query_context/*.query_context.json` | Query result artifacts with ranked chunks, diagnostics, ranker metadata, and KB/PFDS lineage |
| `kbs/manifests/kb_retrieval_summary.md` | Reviewer-facing retrieval summary report |
| `kbs/manifests/kb_bm25_comparison_summary.md` | TF-IDF versus BM25 comparison report |
| `kbs/eval/kb_retrieval_eval_set.json` | Deterministic retrieval evaluation fixture |
| `kbs/manifests/kb_retrieval_eval_results.json` | Machine-readable evaluation result artifact |
| `kbs/manifests/kb_retrieval_eval_summary.md` | Human-readable evaluation summary |

Generated index/query artifacts are ignored by Git:

- `kbs/indexes/`
- `kbs/query_context/`

Manifests, summaries, and evaluation fixtures remain reviewable and may be committed intentionally.

## Latest Verified Pipeline Output

Local clean run completed successfully with:

```text
python -m app.scripts.run_gate5_kb_bm25_eval
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
[gate5:validate] OK
```

Evaluation:

- Cases: 3
- Passed: 3
- Failed: 0

## Ranker Support

Gate 5 adds ranker selection to `query_kb_chunks.py`:

```text
--ranker tfidf
--ranker bm25
```

Default remains:

```text
--ranker tfidf
```

This preserves Gate 3 and Gate 4 behavior.

## BM25 Parameters

Default BM25 parameters:

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

Observed current average document length:

```text
177.710615
```

## Query Context Contract

Gate 5 still emits:

```text
schema_version = kb_chunk_query_context.v2
```

Relevant fields:

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

No query-context schema bump was required because v2 already supports ranker diagnostics and per-term score contributions.

## Important Fix During Gate 5

A no-candidate query path exposed a defect:

- `score_candidates(...)` returned empty ranker diagnostics when there were no candidates,
- `query_index(...)` attempted to read `ranker_diagnostics["ranker"]`,
- the evaluator crashed with `KeyError: 'ranker'` instead of recording a clean failed evaluation case.

Fix:

`score_candidates(...)` now always returns ranker diagnostics, even for zero-candidate queries.

No-result queries now become valid query contexts with:

```text
returned_count = 0
```

The evaluator can then decide pass/fail without crashing.

## Evaluation Fixture

Fixture:

```text
kbs/eval/kb_retrieval_eval_set.json
```

Current cases:

| Case | Query | Ranker | Assertion Type |
|---|---|---|---|
| `usage_rates_unfiltered_bm25` | `rates billing usage` | BM25 | at least one SMDF Usage result |
| `billing_usage_filtered_ccb_bm25` | `rates billing usage` | BM25 | all results are CCB; at least one Billing/Conversion/Case Management result |
| `rates_filtered_smdf_usage_bm25` | `rates` | BM25 | all results are SMDF Usage; at least one expected known bug/patch |

The fixture intentionally validates retrieval lineage behavior. It does not assert business impact conclusions.

## Latest Evaluation Results

Evaluation artifact:

```text
kbs/manifests/kb_retrieval_eval_results.json
```

Result:

```text
case_count = 3
passed_count = 3
failed_count = 0
```

### Case 1 — usage_rates_unfiltered_bm25

Query:

```text
rates billing usage
```

Top result:

| Rank | KB | Bug / Patch | Product | Category | Matched Terms |
|---:|---|---|---|---|---|
| 1 | KB875759 | 39002995 | Oracle Utilities Service and Measurement Data Foundation | Usage | billing, rates, usage |

### Case 2 — billing_usage_filtered_ccb_bm25

Query:

```text
rates billing usage
```

Filter:

```json
{"product": "Oracle Utilities Customer Care and Billing"}
```

Top result:

| Rank | KB | Bug / Patch | Product | Category | Matched Terms |
|---:|---|---|---|---|---|
| 1 | KB869018 | 38848234 | Oracle Utilities Customer Care and Billing | Billing | billing, usage |

### Case 3 — rates_filtered_smdf_usage_bm25

Query:

```text
rates
```

Filter:

```json
{"product": "Oracle Utilities Service and Measurement Data Foundation", "category": "Usage"}
```

Top result:

| Rank | KB | Bug / Patch | Product | Category | Matched Terms |
|---:|---|---|---|---|---|
| 1 | KB875759 | 38794940 | Oracle Utilities Service and Measurement Data Foundation | Usage | rates |

## TF-IDF versus BM25 Findings

Comparison artifact:

```text
kbs/manifests/kb_bm25_comparison_summary.md
```

### Filtered query

Query:

```text
rates billing usage
```

Filter:

```json
{"product": "Oracle Utilities Customer Care and Billing"}
```

Finding:

- Shared top-result chunks: 3
- TF-IDF top chunk: `KB881135::39064768::426d44e375aa6c02d137e52c665b4006f4bd0348738635ec7963e6243ef1ad4e::0003`
- BM25 top chunk: `KB869018::38848234::2ac533785e535054e032320967db5c36f6991d48021825a88a4d5bce8d9f89a0::0003`

### Unfiltered query

Query:

```text
rates billing usage
```

Finding:

- Shared top-result chunks: 0
- TF-IDF top chunk: `KB881135::39109281::c47e693c88ab2fb1d7b10170c77bc18b894e99d7eaa1b568bc3cb9a5d3418cb5::0004`
- BM25 top chunk: `KB875759::39002995::782dd1bd928ad04b242485cc9d6bb0a305bb199e62bd42a09aaa0c70880ec68b::0002`

BM25 materially changes evidence ordering. This is now measurable and reviewable.

## Key Code Added or Updated During Gate 5

| Script / Artifact | Purpose |
|---|---|
| `backend/app/scripts/query_kb_chunks.py` | Adds `--ranker tfidf`, `--ranker bm25`, BM25 diagnostics, and robust no-candidate ranker diagnostics |
| `backend/app/scripts/run_gate5_kb_bm25_eval.py` | Runs Gate 5 BM25 comparison and retrieval evaluation end-to-end |
| `backend/app/scripts/validate_gate5_kb_bm25_eval.py` | Validates recent TF-IDF/BM25 query contexts and BM25 diagnostics |
| `backend/app/scripts/write_kb_bm25_comparison_summary.py` | Produces TF-IDF versus BM25 comparison report |
| `backend/app/scripts/evaluate_kb_retrieval.py` | Runs deterministic retrieval evaluation fixture and emits pass/fail artifacts |
| `kbs/eval/kb_retrieval_eval_set.json` | Initial retrieval evaluation fixture |

## Validation Coverage

Gate 3 validator still checks:

- index exists,
- required SQLite tables exist,
- indexed collection count matches Gate 2,
- indexed chunk count matches Gate 2,
- posting count > 0,
- vocabulary size > 0.

Gate 4 validator still checks:

- query contexts are v2,
- term diagnostics exist,
- source diversity diagnostics exist,
- score contributions exist,
- filtered query results match active filters.

Gate 5 validator checks:

- at least one recent TF-IDF context exists,
- at least one recent BM25 context exists,
- at least one recent filtered TF-IDF context exists,
- at least one recent filtered BM25 context exists,
- BM25 diagnostics include average document length, k1, and b,
- result score contributions exist,
- filtered results match active filters.

Evaluation fixture checks:

- query returns results,
- all-result field constraints,
- any-result field constraints.

## What This Proves

Gate 5 proves that the project can now:

- run deterministic TF-IDF and BM25 retrieval over the same PFDS evidence index,
- expose ranker-specific diagnostics,
- compare ranker outputs side by side,
- measure retrieval behavior with a small pass/fail fixture,
- fail cleanly when an evaluation assumption is unsupported,
- preserve retrieval lineage through all evaluation outputs.

## Known Limitations

Gate 5 remains retrieval-only.

Known limitations:

- Evaluation fixture is small.
- Evaluation assertions are lineage/category/product based, not semantic relevance judgments.
- BM25 parameters are fixed defaults, not tuned.
- There is no phrase/proximity scoring yet.
- There is no hybrid lexical/vector retrieval yet.
- There is no OCR/image understanding for image-heavy PFDS artifacts.
- There is no retrieval API or web UI exposure yet.
- It does not generate upgrade impact analysis.

These limitations are acceptable for Gate 5. They define the next gate.

## Recommended Next Gate

Recommended next gate:

**Gate 6 — Impact Context Assembly**

Gate 6 should not generate impact analysis yet. It should assemble structured evidence packets that later impact generation can consume.

Proposed Gate 6 sequence:

1. Define an impact-context artifact schema:
   - query / target upgrade context,
   - retrieval inputs,
   - selected PFDS chunks,
   - KB lineage,
   - evidence scores,
   - image-bearing flags,
   - missing-evidence warnings,
   - no-claim / no-generation status.
2. Add a deterministic context assembly script:
   - consume retrieval query contexts,
   - select top chunks,
   - group by bug/patch and source PDF,
   - preserve score/ranker diagnostics,
   - include Gate 1 exception warnings where relevant.
3. Add context validation:
   - every selected evidence item has source lineage,
   - every evidence group has KB/bug/product/category,
   - no generated conclusions are present.
4. Add reviewer-facing Markdown report.
5. Only after impact context assembly is stable, add constrained impact-draft generation.

Do not jump to LLM-generated impact analysis yet. Gate 6 should build the evidence packet first.

## Recommended Next Chat Starting Point

Use this prompt to continue in a new chat:

```text
We are continuing work on the Upgrade Impact Analysis Tool.

Gate 1 completed KB source extraction and PFDS evidence mapping.
Gate 2 completed KB PFDS source text extraction and deterministic chunking.
Gate 3 completed KB PFDS lexical retrieval index and query.
Gate 4 completed retrieval diagnostics and controls.
Gate 5 completed deterministic BM25 ranking and retrieval evaluation.

Use this repo as source of truth:
mcstabface/upgrade-impact-tool

Start from these docs/artifacts:
- docs/checkpoints/Gate 1 KB Source Extraction Completion Artifact.md
- docs/checkpoints/Gate 2 KB Search Context Completion Artifact.md
- docs/checkpoints/Gate 3 KB PFDS Retrieval Completion Artifact.md
- docs/checkpoints/Gate 4 KB Retrieval Diagnostics Completion Artifact.md
- docs/checkpoints/Gate 5 BM25 Ranking Evaluation Completion Artifact.md
- kbs/manifests/kb_retrieval_eval_results.json
- kbs/manifests/kb_retrieval_eval_summary.md
- kbs/manifests/kb_bm25_comparison_summary.md
- backend/app/scripts/run_gate5_kb_bm25_eval.py
- backend/app/scripts/evaluate_kb_retrieval.py

Current Gate 5 status:
- 179 indexed PFDS chunk collections
- 895 indexed PFDS chunks
- 79,073 posting rows
- 4,857 vocabulary terms
- TF-IDF and BM25 rankers are supported
- BM25 diagnostics include k1, b, average document length, and score contributions
- BM25 comparison summary is generated
- retrieval evaluation fixture has 3 cases
- evaluation passes with 3 passed / 0 failed
- validators pass with `[gate3:validate] OK`, `[gate4:validate] OK`, and `[gate5:validate] OK`

The Gate 5 pipeline runs successfully with:
python -m app.scripts.run_gate5_kb_bm25_eval

Next recommended gate is Gate 6: Impact Context Assembly.

Please review the repo and produce the next concrete build plan and first patches for Gate 6.
Be specific, repo-grounded, and provide exact patch contents.
```

## Completion Status

Gate 5 is complete for the current source corpus.

The next work should begin from this checkpoint, not from memory.
