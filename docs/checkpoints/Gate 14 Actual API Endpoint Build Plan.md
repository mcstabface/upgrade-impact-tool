# Gate 14 Actual API Endpoint Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Actual API Endpoint or UI Action Binding  
Status: Initial local HTTP endpoint smoke slice  
Generated: 2026-05-13

## Starting Point

Gate 1 completed KB source extraction and PFDS evidence mapping.

Gate 2 completed matched PFDS source text extraction and deterministic chunking.

Gate 3 completed deterministic lexical retrieval over PFDS chunks.

Gate 4 completed retrieval diagnostics and controls.

Gate 5 completed deterministic BM25 ranking and retrieval evaluation.

Gate 6 completed evidence-only impact context assembly.

Gate 7 completed impact context enrichment and draft skeleton.

Gate 8 completed constrained citation-bound impact draft generation.

Gate 9 completed draft review workflow and reviewer export.

Gate 10 completed review decision update commands.

Gate 11 completed read-only review UI surface.

Gate 12 completed mutation bridge with audit trail and artifact regeneration.

Gate 13 completed review update service contract.

Current Gate 13 baseline:

- review mutation request/response service contract exists
- claim and gap update requests are supported
- service calls Gate 12 bridge functions
- service validates review state after mutation
- service regenerates Markdown and HTML reviewer artifacts
- service response validation passes with `[gate13:response] OK`
- mutable review state validates with `[gate10:validate] OK`
- audit trail validates with `[gate12:audit] OK`
- regenerated service surface validates with `[gate11:validate] OK`
- service smoke claim `evidence_group_006` is `REVIEWED / ACCEPT` with visual acknowledgement
- service smoke gap `gap_001` is `ACKNOWLEDGED`
- finalization remains disabled

## Gate 14 Objective

Gate 14 answers this bounded question:

> Can a real local endpoint accept review update requests, call the Gate 13 service contract, and preserve validation/audit/artifact regeneration controls?

Repo inspection did not reveal a stable FastAPI, Flask, Django, React, Vite, or other framework entry point. Therefore the first implementation slice uses Python stdlib HTTP server utilities to add a local endpoint without introducing a framework dependency.

## First Implementation Slice

Added scripts:

| Script | Purpose |
|---|---|
| `backend/app/scripts/review_update_http_server.py` | Local stdlib HTTP endpoint for review updates. |
| `backend/app/scripts/smoke_kb_review_update_http_endpoint.py` | Local HTTP smoke client for health, claim update, and gap update requests. |
| `backend/app/scripts/run_gate14_kb_review_http_endpoint.py` | Starts the local endpoint, runs smoke requests, validates artifacts, and stops the endpoint. |

## Endpoint Contract

Local server:

```bash
python -m app.scripts.review_update_http_server \
  --host 127.0.0.1 \
  --port 8765
```

Routes:

```text
GET /health
POST /review/update
```

### GET /health

Returns:

```json
{
  "status": "OK",
  "service": "kb_review_update",
  "finalization_allowed": false,
  "mutation_contract": "Gate 13 ReviewUpdateRequest"
}
```

### POST /review/update

Accepts the Gate 13 request contract.

Claim update example:

```json
{
  "action": "claim",
  "target_id": "evidence_group_006",
  "value": "ACCEPT",
  "reviewer": "reviewer-id",
  "notes": "Reviewed evidence and visual PFDS content.",
  "visual_acknowledged": true
}
```

Gap acknowledgement example:

```json
{
  "action": "gap",
  "target_id": "gap_001",
  "value": "ACKNOWLEDGED",
  "reviewer": "reviewer-id",
  "notes": "Acknowledged missing PFDS evidence."
}
```

The endpoint calls:

```text
apply_review_update_request(...)
```

and returns the Gate 13 response shape.

On error, it returns JSON with:

```text
status = ERROR
error_type
error
finalization_allowed = false
```

## Gate 14 Smoke Runner

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate14_kb_review_http_endpoint
```

The runner:

1. runs Gate 11 to regenerate the base review surface,
2. copies the base manifest to `kbs/review/kb_draft_review_manifest.gate14_http.json`,
3. starts the local HTTP endpoint as a subprocess,
4. waits for `GET /health`,
5. posts one claim update request,
6. posts one gap acknowledgement request,
7. stops the endpoint,
8. validates mutable review state,
9. validates audit trail,
10. validates regenerated static surface,
11. validates claim response payload,
12. validates gap response payload.

## Generated Outputs

| Artifact | Purpose |
|---|---|
| `kbs/review/kb_draft_review_manifest.gate14_http.json` | HTTP-smoke updated review manifest. |
| `kbs/review/gate14_claim_response.json` | HTTP claim update response. |
| `kbs/review/gate14_gap_response.json` | HTTP gap acknowledgement response. |
| `kbs/manifests/kb_draft_review_export.gate14_http.md` | HTTP-regenerated review export. |
| `kbs/manifests/kb_draft_review_surface.gate14_http.html` | HTTP-regenerated static review surface. |

Generated review JSON remains ignored by Git.

## Acceptance Criteria

Gate 14 initial slice is complete when:

1. `python -m app.scripts.run_gate14_kb_review_http_endpoint` completes successfully.
2. `GET /health` returns status `OK` and `finalization_allowed = false`.
3. `POST /review/update` accepts a claim update request.
4. `POST /review/update` accepts a gap acknowledgement request.
5. Both HTTP responses validate with `[gate13:response] OK`.
6. Mutable review state validates with `[gate10:validate] OK`.
7. Audit trail validates with `[gate12:audit] OK`.
8. Regenerated static surface validates with `[gate11:validate] OK`.
9. Finalization remains disabled.
10. No direct JSON mutation is exposed to browser code.

## Non-Goals

Gate 14 does not:

- introduce a production web framework,
- add browser-side mutation,
- implement authentication or authorization,
- finalize drafts,
- auto-accept claims,
- call an LLM,
- change draft content,
- bypass Gate 10/Gate 12/Gate 13 validators.

## Next Build Steps

### Step 1 — Run Gate 14 locally

```bash
python -m app.scripts.run_gate14_kb_review_http_endpoint
```

Expected validation output includes:

```text
[gate11:validate] OK
[gate14:http-smoke] OK
[gate10:validate] OK
[gate12:audit] OK
[gate11:validate] OK
[gate13:response] OK
[gate13:response] OK
```

### Step 2 — Add Gate 14 completion artifact

After a clean run, add:

```text
docs/checkpoints/Gate 14 Actual API Endpoint Completion Artifact.md
```

### Step 3 — Next gate selection

Recommended next gate after Gate 14 completion:

**Gate 15 — Browser Action Binding or Auth/Role Guard**

Before exposing mutation broadly, decide whether the next step is:

- a browser action that calls the local endpoint, or
- auth/role guard and request provenance controls.

Recommended order: auth/provenance guard before broad browser mutation.

## Notes

Gate 14 deliberately uses a stdlib local HTTP server because no existing app framework entry point was discoverable. This keeps the endpoint real but narrow. It can later be replaced or wrapped by the project’s chosen runtime without changing the Gate 13 service contract.
