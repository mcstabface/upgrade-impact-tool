# Gate 13 Live Review API Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Live Review API or Controlled UI Mutation  
Status: Initial service-contract smoke slice  
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

Current Gate 12 baseline:

- mutation bridge applies claim decisions and gap acknowledgements through Gate 10 functions
- mutation bridge validates review state immediately after mutation
- mutation bridge regenerates Markdown and HTML reviewer artifacts
- mutation bridge records audit events with previous/new state
- audit validation passes with `[gate12:audit] OK`
- bridged review state validates with `[gate10:validate] OK`
- regenerated bridged surface validates with `[gate11:validate] OK`
- smoke claim `evidence_group_006` is `REVIEWED / ACCEPT` with visual acknowledgement
- smoke gap `gap_001` is `ACKNOWLEDGED`
- finalization remains disabled

## Gate 13 Objective

Gate 13 answers this bounded question:

> Can review mutation be exposed through a stable request/response service contract that calls the Gate 12 bridge and returns validated mutation results?

The first implementation slice does not add a live web server because no stable backend API framework entry point was confirmed in repo inspection.

Instead, Gate 13 creates a service module and JSON request/response CLI harness that future live endpoints or UI actions can call.

## First Implementation Slice

Added scripts:

| Script | Purpose |
|---|---|
| `backend/app/scripts/review_update_service.py` | Shared service-layer request/response contract for review mutations. |
| `backend/app/scripts/apply_kb_review_update_service_request.py` | CLI harness that reads request JSON, calls the service contract, writes response JSON, and regenerates artifacts. |
| `backend/app/scripts/validate_kb_review_update_service_response.py` | Validates service response structure and diagnostics. |
| `backend/app/scripts/run_gate13_kb_review_service.py` | Runs Gate 13 service-contract smoke checks. |

## Service Request Contract

Request fields:

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

Supported actions:

```text
claim
gap
```

For `claim` action, `value` must be one of:

```text
ACCEPT
REJECT
NEEDS_MORE_EVIDENCE
UNSET
```

For `gap` action, `value` must be one of:

```text
ACKNOWLEDGED
NEEDS_MORE_EVIDENCE
UNSET
```

Reviewer is required.

## Service Response Contract

Response fields:

```text
status
action
target_id
reviewer
manifest_path
export_path
surface_path
review_status
diagnostics
audit_event_count
messages
```

The response is valid only if:

- status is `OK`,
- action and target ID match the request,
- reviewer is non-empty,
- review status is supported,
- audit event count meets expectation,
- diagnostics review-audit-event count matches response audit count,
- manifest/export/surface paths are returned,
- response messages indicate bridge execution, validation, and artifact regeneration.

## Service Behavior

For each request, the service must:

1. validate request fields,
2. load the review manifest,
3. call Gate 12 bridge functions,
4. write the updated manifest,
5. validate review state,
6. regenerate Markdown review export,
7. regenerate static review surface,
8. return structured response metadata.

The service does not bypass Gate 10/Gate 12 validation.

## Gate 13 Smoke Runner

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate13_kb_review_service
```

The runner:

1. runs Gate 11 to regenerate the base review surface,
2. writes two request payloads:
   - claim accept request for `evidence_group_006`,
   - gap acknowledgement request for `gap_001`,
3. copies the base manifest to `kbs/review/kb_draft_review_manifest.gate13_service.json`,
4. applies the claim request through the service contract,
5. validates the claim response,
6. applies the gap request through the service contract,
7. validates the gap response,
8. validates mutable review state,
9. validates audit trail,
10. validates regenerated static review surface.

## Generated Outputs

| Artifact | Purpose |
|---|---|
| `kbs/review/kb_draft_review_manifest.gate13_service.json` | Smoke-test service-updated review manifest. |
| `kbs/review/gate13_claim_request.json` | Smoke-test claim update request. |
| `kbs/review/gate13_gap_request.json` | Smoke-test gap acknowledgement request. |
| `kbs/review/gate13_claim_response.json` | Smoke-test claim update response. |
| `kbs/review/gate13_gap_response.json` | Smoke-test gap acknowledgement response. |
| `kbs/manifests/kb_draft_review_export.gate13_service.md` | Service-regenerated review export. |
| `kbs/manifests/kb_draft_review_surface.gate13_service.html` | Service-regenerated static review surface. |

Generated review JSON remains ignored by Git.

## Acceptance Criteria

Gate 13 initial slice is complete when:

1. `python -m app.scripts.run_gate13_kb_review_service` completes successfully.
2. Base Gate 11 surface validates with `[gate11:validate] OK`.
3. Claim request applies through service contract.
4. Claim response validates with `[gate13:response] OK`.
5. Gap request applies through service contract.
6. Gap response validates with `[gate13:response] OK`.
7. Mutable review state validates with `[gate10:validate] OK`.
8. Audit trail validates with `[gate12:audit] OK`.
9. Regenerated service surface validates with `[gate11:validate] OK`.
10. Finalization remains disabled.

## Non-Goals

Gate 13 does not:

- add browser-side mutation,
- expose a network API endpoint yet,
- finalize drafts,
- auto-accept claims,
- call an LLM,
- change draft content,
- bypass Gate 10/Gate 12 validators.

## Next Build Steps

### Step 1 — Run Gate 13 locally

```bash
python -m app.scripts.run_gate13_kb_review_service
```

Expected validation output includes:

```text
[gate11:validate] OK
[gate13:response] OK
[gate13:response] OK
[gate10:validate] OK
[gate12:audit] OK
[gate11:validate] OK
```

### Step 2 — Add Gate 13 completion artifact

After a clean run, add:

```text
docs/checkpoints/Gate 13 Live Review API Completion Artifact.md
```

### Step 3 — Next gate selection

Recommended next gate after Gate 13 completion:

**Gate 14 — Actual API Endpoint or UI Action Binding**

Only after Gate 13 response contracts are stable should a live API endpoint or browser action call the service contract.

## Notes

Gate 13 deliberately avoids guessing a web framework that was not discoverable through repo inspection. It creates the service contract a future API can call, which is less glamorous than a button and considerably less likely to ruin everything.
