# Gate 15 Auth Role Guard Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Auth/Role Guard and Request Provenance  
Status: Initial guarded-endpoint smoke slice  
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

Current Gate 14 baseline:

- local HTTP endpoint supports `GET /health`
- local HTTP endpoint supports `POST /review/update`
- endpoint calls Gate 13 service contract
- endpoint preserves Gate 12 bridge behavior
- endpoint validates review state after mutation
- endpoint regenerates Markdown and HTML reviewer artifacts
- endpoint returns structured response JSON
- HTTP claim smoke update accepts `evidence_group_006` with visual acknowledgement
- HTTP gap smoke update acknowledges `gap_001`
- audit trail validates with `[gate12:audit] OK`
- mutable review state validates with `[gate10:validate] OK`
- regenerated HTTP surface validates with `[gate11:validate] OK`
- HTTP responses validate with `[gate13:response] OK`
- finalization remains disabled

## Gate 15 Objective

Gate 15 answers this bounded question:

> Can the local review mutation endpoint reject unauthorized or unprovenanced requests before mutation, while preserving validated mutation, audit, artifact regeneration, and disabled finalization for authorized requests?

Gate 15 adds local development authorization and request provenance controls. It does not implement production authentication, browser mutation, finalization, or role-based enterprise identity integration.

## First Implementation Slice

Added artifacts/scripts:

| File | Purpose |
|---|---|
| `kbs/policies/review_authorization_policy.v1.json` | Local development reviewer/role authorization policy. |
| `backend/app/scripts/review_authorization.py` | Authorization and request provenance helpers. |
| `backend/app/scripts/guarded_review_update_service.py` | Guarded service wrapper around Gate 13 service contract. |
| `backend/app/scripts/guarded_review_update_http_server.py` | Local guarded HTTP endpoint for review updates. |
| `backend/app/scripts/smoke_guarded_kb_review_update_http_endpoint.py` | Smoke client for authorized, denied, and missing-provenance requests. |
| `backend/app/scripts/validate_kb_review_provenance.py` | Validates provenance-bearing audit events. |
| `backend/app/scripts/run_gate15_kb_review_auth_provenance.py` | Runs Gate 15 guarded endpoint smoke checks. |

## Authorization Policy Contract

Policy artifact:

```text
kbs/policies/review_authorization_policy.v1.json
```

Contract:

```text
artifact_type = review_authorization_policy
schema_version = review_authorization_policy.v1
policy_status = LOCAL_DEVELOPMENT_ONLY
finalization_allowed = false
```

Defined roles:

| Role | Allowed Actions | Can Finalize |
|---|---|---|
| `reviewer` | `claim`, `gap` | false |
| `observer` | none | false |

Defined smoke reviewers:

| Reviewer | Role | Status |
|---|---|---|
| `GATE15_AUTH_SMOKE` | reviewer | ACTIVE |
| `GATE15_OBSERVER_SMOKE` | observer | ACTIVE |

## Guarded Endpoint Contract

Local guarded server:

```bash
python -m app.scripts.guarded_review_update_http_server \
  --host 127.0.0.1 \
  --port 8766
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
  "service": "kb_guarded_review_update",
  "authorization_required": true,
  "provenance_required": true,
  "finalization_allowed": false,
  "mutation_contract": "Gate 13 ReviewUpdateRequest + Gate 15 reviewer authorization"
}
```

### POST /review/update

Accepts the Gate 13 review update request body and requires request provenance headers:

```text
X-Request-Id
X-Review-Source
User-Agent
```

Reviewer identity comes from the request body and must be active in the authorization policy.

A request is allowed only if:

- reviewer exists in policy,
- reviewer status is `ACTIVE`,
- reviewer role exists,
- reviewer role allows the requested action,
- reviewer role does not allow finalization,
- request provenance includes `X-Request-Id`.

Denied authorization returns HTTP 403 with:

```text
status = ERROR
authorization_status = DENIED
finalization_allowed = false
```

Missing/invalid provenance returns HTTP 400 with:

```text
status = ERROR
authorization_status = ERROR
finalization_allowed = false
```

## Provenance Audit Contract

Authorized mutations append request provenance to the latest audit event.

Provenance fields:

- request ID,
- endpoint route,
- request source,
- user agent,
- remote address,
- reviewer role,
- reviewer display name.

The review manifest diagnostics include:

```text
provenance_audit_events
```

## Gate 15 Smoke Runner

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate15_kb_review_auth_provenance
```

The runner:

1. runs Gate 11 to regenerate the base review surface,
2. copies the base manifest to `kbs/review/kb_draft_review_manifest.gate15_auth.json`,
3. starts the guarded local HTTP endpoint as a subprocess,
4. waits for `GET /health`,
5. sends an authorized claim update request,
6. sends an observer gap update request that must be denied,
7. sends an authorized gap request without `X-Request-Id` that must be rejected,
8. stops the endpoint,
9. validates mutable review state,
10. validates audit trail,
11. validates provenance audit fields,
12. validates regenerated static surface.

## Generated Outputs

| Artifact | Purpose |
|---|---|
| `kbs/review/kb_draft_review_manifest.gate15_auth.json` | Guarded-smoke updated review manifest. |
| `kbs/review/gate15_authorized_response.json` | Authorized mutation response. |
| `kbs/review/gate15_denied_response.json` | Observer denied mutation response. |
| `kbs/review/gate15_missing_provenance_response.json` | Missing provenance rejection response. |
| `kbs/manifests/kb_draft_review_export.gate15_auth.md` | Guarded-regenerated review export. |
| `kbs/manifests/kb_draft_review_surface.gate15_auth.html` | Guarded-regenerated static review surface. |

Generated review JSON remains ignored by Git.

## Acceptance Criteria

Gate 15 initial slice is complete when:

1. `python -m app.scripts.run_gate15_kb_review_auth_provenance` completes successfully.
2. `GET /health` reports authorization/provenance required and finalization disabled.
3. Authorized reviewer mutation succeeds.
4. Observer mutation is denied before mutation.
5. Missing provenance is rejected before mutation.
6. Mutable review state validates with `[gate10:validate] OK`.
7. Audit trail validates with `[gate12:audit] OK`.
8. Provenance validates with `[gate15:provenance] OK`.
9. Regenerated static surface validates with `[gate11:validate] OK`.
10. Finalization remains disabled.

## Non-Goals

Gate 15 does not:

- implement production authentication,
- implement enterprise identity integration,
- add browser-side mutation,
- finalize drafts,
- add bulk mutation,
- call an LLM,
- bypass Gate 10/Gate 12/Gate 13 validation.

## Next Build Steps

### Step 1 — Run Gate 15 locally

```bash
python -m app.scripts.run_gate15_kb_review_auth_provenance
```

Expected validation output includes:

```text
[gate11:validate] OK
[gate15:http-smoke] OK
[gate10:validate] OK
[gate12:audit] OK
[gate15:provenance] OK
[gate11:validate] OK
```

### Step 2 — Add Gate 15 completion artifact

After a clean run, add:

```text
docs/checkpoints/Gate 15 Auth Role Guard Completion Artifact.md
```

### Step 3 — Next gate selection

Recommended next gate after Gate 15 completion:

**Gate 16 — Browser Action Binding to Guarded Endpoint**

Gate 16 may add a browser-side action only if it calls the guarded endpoint and preserves request provenance.

Do not add browser-side direct JSON mutation.

## Notes

Gate 15 is local-development authorization, not production auth. It makes the mutation path harder to misuse before any browser button gets involved, because apparently we have learned something from the previous fourteen gates. Barely.
