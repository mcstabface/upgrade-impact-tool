# Gate 21C Actual Corpus Demo Readiness Build Plan

## Gate

Gate 21C — Actual Corpus Demo Readiness

## Purpose

Gate 21C adds a read-only assessment for the actual customer corpus rooted at:

```text
kbs/raw
```

The goal is to establish current corpus state before preparing an ingest/retrieval customer demo.

## Why This Gate Exists

Phase 20 hardened retrieval runtime posture. Phase 21 now needs customer-facing demo readiness.

Before building more runtime surfaces, we need to know what is actually present in the corpus and whether it is ready for ingestion assessment.

## Scope

The assessment reports:

- whether `kbs/raw` exists
- total file count
- total byte size
- extension distribution
- deterministic sample file list
- readiness checks
- recommended next steps

## Non-Goals

Gate 21C does not:

- ingest the corpus
- mutate corpus files
- build embeddings
- build indexes
- run retrieval
- enable semantic vector retrieval
- enable hybrid retrieval
- commit generated `kbs/` reports

## Files Planned

```text
backend/app/scripts/actual_corpus_demo_readiness.py
backend/app/scripts/validate_actual_corpus_demo_readiness.py
backend/app/scripts/run_gate21c_actual_corpus_demo_readiness.py
docs/checkpoints/Gate 21C Actual Corpus Demo Readiness Build Plan.md
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate21c_actual_corpus_demo_readiness
```

## Expected Validation Output

```text
[gate21c:actual-corpus] OK
[gate21c:actual-corpus] missing_root=not_ready
[gate21c:actual-corpus] empty_root=not_ready
[gate21c:actual-corpus] populated_root=ready_for_ingestion_assessment
[gate21c:actual-corpus] Wrote demo readiness report: .../kbs/retrieval/kb_actual_corpus_demo_readiness.v1.json
[gate21c:actual-corpus] status=ACTUAL_CORPUS_READY_FOR_INGESTION_ASSESSMENT
[gate21c:actual-corpus] corpus_root=kbs/raw
[gate21c:actual-corpus] corpus_root_exists=true
[gate21c] Pipeline complete
[gate21c] Actual corpus demo readiness assessment completed for kbs/raw
```

The exact file count, total size, and extension count depend on the local corpus.

## Runtime Artifact

The runner writes a local generated report:

```text
kbs/retrieval/kb_actual_corpus_demo_readiness.v1.json
```

This report is a runtime artifact and should not be committed.

## Completion Criteria

Gate 21C is complete when:

1. Readiness reporter exists.
2. Validator covers missing, empty, and populated corpus roots.
3. Runner validates and reports against `kbs/raw`.
4. Local validation passes.
5. PR diff contains only Gate 21C source and checkpoint files.
6. No generated `kbs/` artifacts are committed.

## Next Gate Candidate

Gate 21D — Actual Corpus Ingestion Dry Run or Demo Query Candidate Capture
