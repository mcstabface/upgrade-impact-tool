# Gate 16C Guarded Endpoint Security Audit Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: Guarded Endpoint Uses Auth Adapter and Security Denial Audit  
Status: Complete for current sample corpus  
Generated: 2026-05-13

## Purpose

This checkpoint captures the completed state of Gate 16C for the KB ingestion/customization phase.

Gate 16C answered this bounded question:

> Can the guarded local endpoint use the Gate 16B auth adapter and write security-denial audit events for denied endpoint requests while preserving authorized mutation behavior?

For the current implementation slice, the answer is yes.

Gate 16C wires the guarded endpoint to the Gate 16B adapter/audit seam. It does not implement production OIDC, reverse-proxy asserted identity, signed service tokens, browser mutation, finalization, or LLM-assisted review decisions.

## Source Baseline

Gate 16C starts from Gate 16B auth adapter interface and security denial audit events.

Current Gate 16B baseline:

- auth adapter protocol exists
- authenticated principal dataclass exists
- reviewer identity dataclass exists
- authorization decision dataclass exists
- local policy auth adapter exists
- security denial audit JSONL writer exists
- security denial audit validator exists
- generated audit output is ignored under `kbs/audit/`
- smoke runner authorizes `GATE15_AUTH_SMOKE`
- smoke runner denies `GATE15_OBSERVER_SMOKE`
- smoke runner denies `UNKNOWN_REVIEWER`
- denied requests write security denial audit events
- denial audit validates with `[gate16b:audit] OK`
- finalization remains disabled

## Gate 16C Pipeline

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate16c_guarded_endpoint_security_audit
```

Dry run:

```bash
python -m app.scripts.run_gate16c_guarded_endpoint_security_audit --dry-run
```

The runner performs these steps:

1. runs `app.scripts.run_gate11_kb_review_surface`,
2. copies the base review manifest to `kbs/review/kb_draft_review_manifest.gate16c_auth.json`,
3. starts `app.scripts.guarded_review_update_http_server` with `--security-audit-output kbs/audit/security_denials.gate16c.jsonl`,
4. runs `app.scripts.smoke_guarded_kb_review_update_http_endpoint`,
5. stops the guarded endpoint,
6. validates mutable review state,
7. validates authorized mutation audit trail,
8. validates authorized mutation provenance,
9. validates endpoint-level security denial audit,
10. validates regenerated static review surface.

## Generated Artifacts

| Artifact | Purpose |
|---|---|
| `kbs/review/kb_draft_review_manifest.gate16c_auth.json` | Gate 16C guarded endpoint review manifest |
| `kbs/review/gate16c_authorized_response.json` | Authorized mutation response |
| `kbs/review/gate16c_denied_response.json` | Observer denied response |
| `kbs/review/gate16c_missing_provenance_response.json` | Missing provenance response |
| `kbs/manifests/kb_draft_review_export.gate16c_auth.md` | Guarded-regenerated review export |
| `kbs/manifests/kb_draft_review_surface.gate16c_auth.html` | Guarded-regenerated static review surface |
| `kbs/audit/security_denials.gate16c.jsonl` | Endpoint-level security denial audit log |

Generated review and audit JSON/JSONL artifacts remain ignored by Git:

```text
kbs/review/
kbs/audit/
```

The Markdown/HTML smoke artifacts may be committed intentionally for review.

## Latest Verified Pipeline Output

Local clean run completed successfully with:

```text
python -m app.scripts.run_gate16c_guarded_endpoint_security_audit
```

Expected validation sequence:

```text
[gate11:validate] OK
[gate15:http-smoke] OK
[gate10:validate] OK
[gate12:audit] OK
[gate15:provenance] OK
[gate16b:audit] OK
[gate11:validate] OK
```

Pushed review export state:

- Artifact type: `kb_draft_review_manifest`
- Schema version: `kb_draft_review_manifest.v1`
- Review status: `IN_REVIEW`
- Claim review tasks: 15
- Evidence review tasks: 13
- Visual review tasks: 13
- Unresolved gap tasks: 10
- Finalization allowed: `False`

## Endpoint Changes

Updated script:

```text
backend/app/scripts/guarded_review_update_http_server.py
```

The guarded endpoint now reports on health:

```text
security_denial_audit_enabled = true
mutation_contract = Gate 13 ReviewUpdateRequest + Gate 16B auth adapter
```

`POST /review/update` now:

1. parses the Gate 13 review update request,
2. calls `LocalPolicyAuthAdapter.authorize_request_context(...)`,
3. appends a security denial audit event if authorization is denied,
4. appends a security denial audit event if request provenance is invalid,
5. calls the existing guarded mutation path for authorized/provenanced requests,
6. preserves the existing mutation audit/provenance behavior for authorized requests.

## Duplicate Audit Guard

Gate 16C introduced an `AuditedPermissionError` marker to prevent duplicate security-denial audit entries for the same denied endpoint request.

This matters because authorization denials are now written as security audit events before the endpoint returns an HTTP error response.

## Authorized Mutation Result

The authorized smoke request uses:

```text
reviewer = GATE15_AUTH_SMOKE
action = claim
target = evidence_group_006
request_id = gate15-request-0001
```

Result:

```text
review_status = REVIEWED
reviewer_decision = ACCEPT
visual_acknowledgement_status = ACKNOWLEDGED
reviewer = GATE15_AUTH_SMOKE
```

The accepted claim cites image-bearing evidence, so visual acknowledgement remains required and recorded.

## Denied Endpoint Results

The guarded smoke client also submits two denied/rejected requests.

### Observer Denial

Request:

```text
reviewer = GATE15_OBSERVER_SMOKE
action = gap
target = gap_001
```

Result:

```text
HTTP 403
authorization_status = DENIED
security denial audit event written
no review mutation applied
```

### Missing Provenance Rejection

Request:

```text
reviewer = GATE15_AUTH_SMOKE
action = gap
target = gap_001
missing header = X-Request-Id
```

Result:

```text
HTTP 400
authorization_status = ERROR
security denial audit event written
no review mutation applied
```

## Review Mutation State

The pushed review export confirms:

- `evidence_group_006` is `REVIEWED / ACCEPT`,
- visual acknowledgement is `ACKNOWLEDGED`,
- reviewer is `GATE15_AUTH_SMOKE`,
- `gap_001` remains `PENDING_ACKNOWLEDGEMENT / UNSET`,
- all other unresolved gaps remain unset,
- one review mutation audit event exists,
- finalization remains disabled.

This demonstrates that denied and invalid-provenance requests did not mutate review state.

## Security Denial Audit Contract

Endpoint-level security denial audit output:

```text
kbs/audit/security_denials.gate16c.jsonl
```

Each event is written by:

```text
backend/app/scripts/security_denial_audit.py
```

Each event includes:

- event ID,
- timestamp UTC,
- event type `SECURITY_DENIAL`,
- request ID or `MISSING_REQUEST_ID`,
- route,
- action,
- target ID,
- reviewer ID,
- principal subject,
- principal issuer,
- decision `DENIED`,
- denial reason,
- source,
- user agent,
- finalization allowed flag set to false,
- previous hash,
- event hash.

The security denial audit validates with:

```text
[gate16b:audit] OK
```

Denied endpoint requests create security denial audit events, not review mutation audit events.

## Regenerated Review Surface

The pushed static review surface confirms:

- review status is `IN_REVIEW`,
- claim tasks: 15,
- evidence review tasks: 13,
- visual review tasks: 13,
- unresolved gap tasks: 10,
- finalization allowed: `False`,
- `evidence_group_006` is accepted,
- the surface remains read-only.

## Key Code Added or Updated During Gate 16C

| Script / Artifact | Purpose |
|---|---|
| `backend/app/scripts/guarded_review_update_http_server.py` | Uses `LocalPolicyAuthAdapter` and writes endpoint-level security denial audit events |
| `backend/app/scripts/run_gate16c_guarded_endpoint_security_audit.py` | Runs endpoint-level auth/audit smoke pipeline |
| `docs/checkpoints/Gate 16C Guarded Endpoint Security Audit Build Plan.md` | Captures Gate 16C build plan and acceptance criteria |

## Validation Coverage

Gate 16C validates that:

- base Gate 11 surface still validates,
- guarded endpoint health succeeds,
- authorized reviewer mutation succeeds,
- observer mutation is denied before review mutation,
- missing request ID is rejected before review mutation,
- mutable review state validates after authorized mutation,
- review mutation audit validates after authorized mutation,
- review provenance validates after authorized mutation,
- endpoint security denial audit validates with at least two events,
- regenerated static review surface validates,
- finalization remains disabled.

## What This Proves

Gate 16C proves that the project can now:

- route endpoint authorization through the auth adapter seam,
- write security-denial audit events for endpoint denials,
- write security-denial audit events for invalid-provenance endpoint requests,
- preserve authorized mutation behavior,
- keep review mutation audit separate from security denial audit,
- validate denied-request audit hash chains,
- preserve read-only reviewer artifacts,
- keep finalization disabled.

## Known Limitations

Gate 16C remains local/prototype infrastructure.

Known limitations:

- It does not implement production OIDC.
- It does not implement reverse-proxy identity trust.
- It does not implement signed service tokens.
- It does not add browser mutation.
- It does not expose a production web framework.
- It does not finalize drafts.
- It does not call an LLM.

These limitations are acceptable for Gate 16C. They define the next gate.

## Recommended Next Gate

Recommended next gate:

**Gate 17 — Browser Action Scaffold Against Guarded Endpoint**

Gate 17 may add browser-side scaffolding only if it calls the guarded endpoint and does not directly mutate JSON.

Proposed Gate 17 sequence:

1. Add a generated static action scaffold or local HTML form disabled by default.
2. Require reviewer identity, request ID, visual acknowledgement, and endpoint URL.
3. Use `POST /review/update` only.
4. Preserve no-finalization controls.
5. Add smoke documentation for manual local browser testing.
6. Keep direct JSON mutation forbidden.

Alternative next gate:

**Gate 17A — OIDC Adapter Skeleton**

If production-hardening remains the priority, add an OIDC adapter skeleton behind the `AuthAdapter` protocol without enabling it.

## Recommended Next Chat Starting Point

Use this prompt to continue in a new chat:

```text
We are continuing work on the Upgrade Impact Analysis Tool.

Gate 1 completed KB source extraction and PFDS evidence mapping.
Gate 2 completed KB PFDS source text extraction and deterministic chunking.
Gate 3 completed KB PFDS lexical retrieval index and query.
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
Gate 14 completed local HTTP review update endpoint.
Gate 15 completed auth/role guard and request provenance for local endpoint.
Gate 16A completed production auth design spec.
Gate 16B completed auth adapter interface and security denial audit events.
Gate 16C completed guarded endpoint security-denial audit wiring.

Use this repo as source of truth:
mcstabface/upgrade-impact-tool

Start from these docs/artifacts:
- docs/checkpoints/Gate 1 KB Source Extraction Completion Artifact.md
- docs/checkpoints/Gate 2 KB Search Context Completion Artifact.md
- docs/checkpoints/Gate 3 KB PFDS Retrieval Completion Artifact.md
- docs/checkpoints/Gate 4 KB Retrieval Diagnostics Completion Artifact.md
- docs/checkpoints/Gate 5 BM25 Ranking Evaluation Completion Artifact.md
- docs/checkpoints/Gate 6 Impact Context Assembly Completion Artifact.md
- docs/checkpoints/Gate 7 Impact Context Enrichment Completion Artifact.md
- docs/checkpoints/Gate 8 Constrained Impact Draft Completion Artifact.md
- docs/checkpoints/Gate 9 Draft Review Workflow Completion Artifact.md
- docs/checkpoints/Gate 10 Review Decision Update Commands Completion Artifact.md
- docs/checkpoints/Gate 11 Review UI Surface Completion Artifact.md
- docs/checkpoints/Gate 12 UI Mutation Bridge Completion Artifact.md
- docs/checkpoints/Gate 13 Live Review API Completion Artifact.md
- docs/checkpoints/Gate 14 Actual API Endpoint Completion Artifact.md
- docs/checkpoints/Gate 15 Auth Role Guard Completion Artifact.md
- docs/checkpoints/Gate 16A Production Auth Design Completion Artifact.md
- docs/checkpoints/Gate 16B Auth Adapter Security Audit Completion Artifact.md
- docs/checkpoints/Gate 16C Guarded Endpoint Security Audit Completion Artifact.md
- backend/app/scripts/guarded_review_update_http_server.py
- backend/app/scripts/run_gate16c_guarded_endpoint_security_audit.py
- backend/app/scripts/auth_adapter.py
- backend/app/scripts/local_policy_auth_adapter.py
- backend/app/scripts/security_denial_audit.py
- backend/app/scripts/validate_security_denial_audit.py
- kbs/manifests/kb_draft_review_export.gate16c_auth.md
- kbs/manifests/kb_draft_review_surface.gate16c_auth.html

Current Gate 16C status:
- guarded endpoint preflights authorization through `LocalPolicyAuthAdapter`
- endpoint health reports security-denial audit enabled
- authorized reviewer mutation still succeeds
- observer mutation is denied before review mutation
- missing request ID is rejected before review mutation
- endpoint denials write security denial audit events
- security denial audit validates with `[gate16b:audit] OK`
- review mutation audit validates with `[gate12:audit] OK`
- review provenance validates with `[gate15:provenance] OK`
- mutable review state validates with `[gate10:validate] OK`
- regenerated guarded surface validates with `[gate11:validate] OK`
- finalization remains disabled

The Gate 16C pipeline runs successfully with:
python -m app.scripts.run_gate16c_guarded_endpoint_security_audit

Next recommended gate is Gate 17: Browser Action Scaffold Against Guarded Endpoint, or Gate 17A: OIDC Adapter Skeleton.

Please review the repo and produce the next concrete build plan and first patches for Gate 17 or 17A.
Be specific, repo-grounded, and provide exact patch contents.
```

## Completion Status

Gate 16C is complete for the current implementation slice.

The next work should begin from this checkpoint, not from memory.
