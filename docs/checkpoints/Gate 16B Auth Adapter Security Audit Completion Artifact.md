# Gate 16B Auth Adapter Security Audit Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: Auth Adapter Interface and Security Audit Events  
Status: Complete for current sample corpus  
Generated: 2026-05-13

## Purpose

This checkpoint captures the completed state of Gate 16B for the KB ingestion/customization phase.

Gate 16B answered this bounded question:

> Can we introduce code-level auth adapter interfaces and security-denial audit events without committing to a production identity provider?

For the current implementation slice, the answer is yes.

Gate 16B adds an auth adapter seam and a security-denial audit stream. It does not implement OIDC, reverse-proxy asserted identity, signed service tokens, browser mutation, finalization, or LLM-assisted review decisions.

## Source Baseline

Gate 16B starts from Gate 16A production auth design spec.

Current Gate 16A baseline:

- production auth design spec exists
- local Gate 15 is explicitly scoped as non-production auth
- OIDC, reverse-proxy identity, and signed service-token patterns are documented
- reviewer identity must be derived from authenticated principal data in production
- production role model is documented
- permission checks are documented
- production provenance requirements are documented
- audit hardening requirements are documented
- browser mutation requirements are documented
- production readiness gates are documented
- validator passes with `[gate16a:validate] OK`
- finalization remains disabled

## Gate 16B Pipeline

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate16b_auth_adapter_security_audit
```

Dry run:

```bash
python -m app.scripts.run_gate16b_auth_adapter_security_audit --dry-run
```

The runner performs these checks:

1. authorizes `GATE15_AUTH_SMOKE` for claim mutation,
2. confirms reviewer identity is derived through the local adapter,
3. denies `GATE15_OBSERVER_SMOKE` for gap mutation,
4. writes a security denial audit event for observer denial,
5. denies `UNKNOWN_REVIEWER` before authorization,
6. writes a security denial audit event for unknown reviewer denial,
7. validates the security denial audit JSONL with at least two events.

## Generated / Updated Artifacts

| Artifact | Purpose |
|---|---|
| `backend/app/scripts/auth_adapter.py` | Authenticated principal, reviewer identity, authorization decision dataclasses, and auth adapter protocol |
| `backend/app/scripts/local_policy_auth_adapter.py` | Local policy adapter implementing principal-to-reviewer authorization against the Gate 15 local policy artifact |
| `backend/app/scripts/security_denial_audit.py` | Append-only JSONL security denial audit writer with hash chaining |
| `backend/app/scripts/validate_security_denial_audit.py` | Validates denial audit JSONL structure and hash chain |
| `backend/app/scripts/run_gate16b_auth_adapter_security_audit.py` | Runs auth adapter and denial audit smoke checks |
| `.gitignore` | Ignores generated `kbs/audit/` outputs |
| `docs/checkpoints/Gate 16B Auth Adapter Security Audit Build Plan.md` | Build plan and acceptance criteria for Gate 16B |

Generated security audit output:

```text
kbs/audit/security_denials.gate16b.jsonl
```

Generated audit outputs remain ignored by Git:

```text
kbs/audit/
```

## Latest Verified Pipeline Output

Local clean run completed successfully with:

```text
python -m app.scripts.run_gate16b_auth_adapter_security_audit
```

Observed output:

```text
[gate16b] Starting auth adapter / security audit pipeline
[gate16b] Repository root: /home/stabby/Documents/upgrade-impact-tool
[gate16b] Smoke local policy auth adapter
[gate16b] Wrote security denial audit: /home/stabby/Documents/upgrade-impact-tool/kbs/audit/security_denials.gate16b.jsonl
[gate16b]   /home/stabby/Documents/upgrade-impact-tool/backend/.venv/bin/python -m app.scripts.validate_security_denial_audit --audit /home/stabby/Documents/upgrade-impact-tool/kbs/audit/security_denials.gate16b.jsonl --min-events 2
[gate16b:audit] OK
[gate16b:audit] audit=/home/stabby/Documents/upgrade-impact-tool/kbs/audit/security_denials.gate16b.jsonl
[gate16b:audit] min_events=2
[gate16b] Pipeline complete
[gate16b] Output: /home/stabby/Documents/upgrade-impact-tool/kbs/audit/security_denials.gate16b.jsonl
```

## Auth Adapter Contract

Script:

```text
backend/app/scripts/auth_adapter.py
```

Primary dataclasses:

```text
AuthenticatedPrincipal
ReviewerIdentity
AuthorizationDecision
```

Protocol:

```text
AuthAdapter
```

Required methods:

```text
get_authenticated_principal(request_context)
map_principal_to_reviewer(principal)
authorize_action(reviewer, action)
```

This is the code seam for future auth providers:

- OIDC adapter,
- reverse-proxy asserted identity adapter,
- signed service-token adapter.

## Local Policy Adapter

Script:

```text
backend/app/scripts/local_policy_auth_adapter.py
```

The local adapter uses:

```text
kbs/policies/review_authorization_policy.v1.json
```

It maps:

```text
request_context.reviewer_id
  -> AuthenticatedPrincipal
  -> ReviewerIdentity
  -> AuthorizationDecision
```

This is still local-development behavior. It is not production authentication.

## Smoke Authorization Results

### Authorized Reviewer

Request context:

```text
reviewer_id = GATE15_AUTH_SMOKE
action = claim
```

Result:

```text
allowed = true
principal_issuer = local-policy
```

This proves the allowed path now passes through the adapter seam and produces a principal-derived reviewer identity, however cardboard the local principal still is.

### Observer Denial

Request context:

```text
reviewer_id = GATE15_OBSERVER_SMOKE
action = gap
```

Result:

```text
allowed = false
security denial audit event written
```

### Unknown Reviewer Denial

Request context:

```text
reviewer_id = UNKNOWN_REVIEWER
action = claim
```

Result:

```text
PermissionError
security denial audit event written
```

## Security Denial Audit Contract

Writer:

```text
backend/app/scripts/security_denial_audit.py
```

Default output:

```text
kbs/audit/security_denials.jsonl
```

Gate 16B smoke output:

```text
kbs/audit/security_denials.gate16b.jsonl
```

Each event includes:

- event ID,
- timestamp UTC,
- event type,
- request ID,
- route,
- action,
- target ID,
- reviewer ID,
- principal subject,
- principal issuer,
- decision,
- denial reason,
- source,
- user agent,
- finalization allowed flag,
- previous hash,
- event hash.

Security denial events are separate from review mutation audit events.

Denied requests do not create review mutation audit events.

## Hash Chain

Security denial audit events are hash-linked:

```text
GENESIS -> event_hash_0001 -> event_hash_0002 -> ...
```

The validator recomputes each event hash after removing `event_hash` from the payload and verifies that each `previous_hash` points to the previous event.

## Validation Coverage

Validator:

```text
backend/app/scripts/validate_security_denial_audit.py
```

Validation checks:

- audit file exists,
- minimum event count is present,
- required event fields exist,
- event type is `SECURITY_DENIAL`,
- decision is `DENIED`,
- finalization allowed is `false`,
- event IDs are unique,
- previous hash chain starts at `GENESIS`,
- each event hash matches the canonical event payload.

Latest validation:

```text
[gate16b:audit] OK
```

## What This Proves

Gate 16B proves that the project can now:

- represent authenticated principals independently from local reviewer IDs,
- map principals to reviewer identities,
- authorize actions through a provider-shaped adapter seam,
- preserve the local policy implementation for smoke testing,
- record denied authorization attempts separately from review mutation audit,
- hash-chain denial audit events,
- keep finalization disabled in denial audit records.

## Known Limitations

Gate 16B remains adapter/audit infrastructure only.

Known limitations:

- The guarded endpoint does not use the adapter yet.
- Denial audit is not yet wired into endpoint-level failures.
- It does not implement OIDC.
- It does not implement reverse-proxy identity trust.
- It does not implement signed service tokens.
- It does not add browser mutation.
- It does not finalize drafts.
- It does not call an LLM.

These limitations are acceptable for Gate 16B. They define the next gate.

## Recommended Next Gate

Recommended next gate:

**Gate 16C — Guarded Endpoint Uses Auth Adapter and Security Denial Audit**

Gate 16C should wire the Gate 15 guarded endpoint to the Gate 16B auth adapter and security denial audit writer so denied endpoint requests produce security audit events consistently.

Proposed Gate 16C sequence:

1. Refactor guarded endpoint authorization to call `LocalPolicyAuthAdapter`.
2. On authorization denial, append a security denial audit event.
3. On missing/invalid provenance, append a security denial audit event where possible.
4. Preserve existing Gate 15 behavior for authorized mutation.
5. Extend smoke runner to validate endpoint-level denial audit output.
6. Keep finalization disabled.

Do not add browser mutation until endpoint-level security denial auditing is wired.

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
- backend/app/scripts/auth_adapter.py
- backend/app/scripts/local_policy_auth_adapter.py
- backend/app/scripts/security_denial_audit.py
- backend/app/scripts/validate_security_denial_audit.py
- backend/app/scripts/run_gate16b_auth_adapter_security_audit.py

Current Gate 16B status:
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

The Gate 16B pipeline runs successfully with:
python -m app.scripts.run_gate16b_auth_adapter_security_audit

Next recommended gate is Gate 16C: Guarded Endpoint Uses Auth Adapter and Security Denial Audit.

Please review the repo and produce the next concrete build plan and first patches for Gate 16C.
Be specific, repo-grounded, and provide exact patch contents.
```

## Completion Status

Gate 16B is complete for the current implementation slice.

The next work should begin from this checkpoint, not from memory.
