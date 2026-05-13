# Gate 16C Guarded Endpoint Security Audit Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Guarded Endpoint Uses Auth Adapter and Security Denial Audit  
Status: Initial endpoint wiring slice  
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

Gate 14 completed local HTTP review update endpoint.

Gate 15 completed auth/role guard and request provenance for local endpoint.

Gate 16A completed production auth design spec.

Gate 16B completed auth adapter interface and security denial audit events.

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

## Gate 16C Objective

Gate 16C answers this bounded question:

> Can the guarded local endpoint use the Gate 16B auth adapter and write security-denial audit events for denied endpoint requests while preserving authorized mutation behavior?

Gate 16C wires the endpoint to the adapter/audit seam. It does not implement production auth, browser mutation, finalization, or LLM-assisted review decisions.

## First Implementation Slice

Updated/added:

| File | Purpose |
|---|---|
| `backend/app/scripts/guarded_review_update_http_server.py` | Now preflights authorization with `LocalPolicyAuthAdapter` and appends security denial audit events for endpoint denials. |
| `backend/app/scripts/run_gate16c_guarded_endpoint_security_audit.py` | Runs endpoint-level authorized mutation, denied requests, mutation audit validation, provenance validation, security denial audit validation, and surface validation. |

## Endpoint Changes

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

## Security Denial Audit Behavior

Endpoint-level denied requests write to a configured audit path:

```text
--security-audit-output
```

Gate 16C smoke output:

```text
kbs/audit/security_denials.gate16c.jsonl
```

Denied endpoint requests produce `SECURITY_DENIAL` audit events with:

- request ID or `MISSING_REQUEST_ID`,
- route,
- action,
- target ID,
- reviewer ID,
- principal subject,
- principal issuer,
- denial reason,
- source,
- user agent,
- finalization allowed set to false,
- hash-chain fields.

Denied endpoint requests do not create review mutation audit events.

## Gate 16C Smoke Runner

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate16c_guarded_endpoint_security_audit
```

The runner:

1. runs Gate 11 to regenerate the base review surface,
2. copies the base manifest to `kbs/review/kb_draft_review_manifest.gate16c_auth.json`,
3. starts the guarded endpoint with `--security-audit-output kbs/audit/security_denials.gate16c.jsonl`,
4. runs the guarded smoke client:
   - authorized reviewer mutation succeeds,
   - observer mutation is denied,
   - missing request ID is rejected,
5. stops the endpoint,
6. validates mutable review state,
7. validates authorized mutation audit trail,
8. validates authorized mutation provenance,
9. validates endpoint security denial audit with at least two events,
10. validates regenerated static review surface.

## Generated Outputs

| Artifact | Purpose |
|---|---|
| `kbs/review/kb_draft_review_manifest.gate16c_auth.json` | Gate 16C guarded endpoint review manifest. |
| `kbs/review/gate16c_authorized_response.json` | Authorized mutation response. |
| `kbs/review/gate16c_denied_response.json` | Observer denied response. |
| `kbs/review/gate16c_missing_provenance_response.json` | Missing provenance response. |
| `kbs/manifests/kb_draft_review_export.gate16c_auth.md` | Guarded-regenerated review export. |
| `kbs/manifests/kb_draft_review_surface.gate16c_auth.html` | Guarded-regenerated static review surface. |
| `kbs/audit/security_denials.gate16c.jsonl` | Endpoint-level security denial audit log. |

Generated review/audit JSON remains ignored by Git.

## Acceptance Criteria

Gate 16C initial slice is complete when:

1. `python -m app.scripts.run_gate16c_guarded_endpoint_security_audit` completes successfully.
2. Endpoint health reports security-denial audit enabled.
3. Authorized reviewer mutation succeeds.
4. Observer mutation is denied before mutation.
5. Missing request ID is rejected before mutation.
6. Review mutation audit validates with `[gate12:audit] OK`.
7. Review provenance validates with `[gate15:provenance] OK`.
8. Security denial audit validates with `[gate16b:audit] OK`.
9. Regenerated static surface validates with `[gate11:validate] OK`.
10. Finalization remains disabled.

## Non-Goals

Gate 16C does not:

- implement production OIDC,
- implement reverse-proxy identity trust,
- implement signed service tokens,
- add browser mutation,
- finalize drafts,
- call an LLM.

## Recommended Next Gate

Recommended next gate:

**Gate 17 — Browser Action Scaffold Against Guarded Endpoint**

Gate 17 may add browser-side scaffolding only if it calls the guarded endpoint and does not directly mutate JSON.

Proposed sequence:

1. Add a generated static action scaffold or local HTML form disabled by default.
2. Require reviewer identity, request ID, visual acknowledgement, and endpoint URL.
3. Use `POST /review/update` only.
4. Preserve no-finalization controls.
5. Add smoke documentation for manual local browser testing.

Alternative:

**Gate 17A — OIDC Adapter Skeleton**

If production-hardening remains the priority, add an OIDC adapter skeleton behind the `AuthAdapter` protocol without enabling it.

## Notes

Gate 16C makes the endpoint use the notebook we gave it in Gate 16B. This is the part where the doorman is no longer allowed to wave people away without writing down why. Civilization, such as it is.
