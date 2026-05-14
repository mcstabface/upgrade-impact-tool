# Gate 18U Vector Query Result Citation Join Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Vector Query Result Citation Join  
Status: Proposed  
Generated: 2026-05-14

## Purpose

Gate 18U joins fixture vector similarity query results back to citation payloads from the full-text embedding request payload.

This gate remains fixture-only. It does not enable production semantic retrieval and does not call an embedding model.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/vector_query_result_citation_join.py` | Joins fixture vector query results to request rows and citation payloads |
| `backend/app/scripts/validate_vector_query_result_citation_join.py` | Validates complete joins, missing citation reporting, and query-status fail-closed behavior |
| `backend/app/scripts/run_gate18u_vector_query_result_citation_join.py` | Gate runner |

## Source Artifacts

Gate 18U requires:

```text
kbs/retrieval/kb_fixture_vector_similarity_query.v1.json
kbs/retrieval/kb_embedding_full_text_requests.v1.jsonl
```

Gate 18U writes locally:

```text
kbs/retrieval/kb_fixture_vector_citation_join.v1.json
```

## Join Behavior

Gate 18U validates:

```text
query report status must be FIXTURE_VECTOR_QUERY_OK
production_retrieval_enabled remains false
query results join by chunk_id
joined results preserve rank order
joined results include request_id
joined results include text_hash
joined results include citation_payload
missing citation payloads are reported
bad query status fails closed
```

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate18u_vector_query_result_citation_join
```

Expected output:

```text
[gate18u:citation-join] OK
[gate18u:citation-join] query_results=joined
[gate18u:citation-join] citations=present
[gate18u:citation-join] missing_citation=reported
[gate18u:citation-join] production_retrieval_enabled=false
```

Recommended next gate: **Gate 18V — Citation-Bound Vector Context Assembly**.
