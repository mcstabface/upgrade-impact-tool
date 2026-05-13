# Gate 16B Auth Adapter Security Audit Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Auth Adapter Interface and Security Audit Events  
Status: Initial auth-adapter/security-denial-audit slice  
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

## Gate 16B Objective

Gate 16B answers this bounded question:

> Can we introduce code-level auth adapter interfaces and security-denial audit events without committing to a production identity provider?

Gate 16B adds an adapter seam and denial audit stream. It does not implement production OIDC, proxy identity, signed service tokens, or browser mutation.

## First Implementation Slice

Added/updated:

| File | Purpose |
|---|---|
| `backend/app/scripts/auth_adapter.py` | Authenticated principal, reviewer identity, authorization decision dataclasses, and auth adapter protocol. |
| `backend/app/scripts/local_policy_auth_adapter.py` | Local policy adapter implementing principal-to-reviewer authorization against the Gate 15 local policy artifact. |
| `backend/app/scripts/security_denial_audit.py` | Append-only JSONL security denial audit writer with hash chaining. |
| `backend/app/scripts/validate_security_denial_audit.py` | Validates denial audit JSONL structure and hash chain. |
| `backend/app/scripts/run_gate16b_auth_adapter_security_audit.py` | Runs auth adapter and denial audit smoke checks. |
| `.gitignore` | Ignores generated `kbs/audit/` outputs. |

## Auth Adapter Contract

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

This is the seam where future OIDC, reverse-proxy, or signed-token adapters should plug in.

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
request_context.reviewer_id -> AuthenticatedPrincipal -> ReviewerIdentity -> AuthorizationDecision
```

This remains local-development behavior and is not production authentication.

## Security Denial Audit Contract

Security denial audit writer:

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

Hash chain:

```text
GENESIS -> event_hash_0001 -> event_hash_0002 -> ...
```

Security denial audit events are separate from review mutation audit events.

## Gate 16B Smoke Runner

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate16b_auth_adapter_security_audit
```

The runner:

1. authorizes `GATE15_AUTH_SMOKE` for claim mutation,
2. confirms the resulting reviewer identity is derived through the local adapter,
3. denies `GATE15_OBSERVER_SMOKE` for gap mutation,
4. writes security denial audit event for observer denial,
5. denies `UNKNOWN_REVIEWER` before authorization,
6. writes security denial audit event for unknown reviewer denial,
7. validates the denial audit JSONL with at least two events.

## Generated Outputs

| Artifact | Purpose |
|---|---|
| `kbs/audit/security_denials.gate16b.jsonl` | Gate 16B smoke security denial audit log. |

Generated audit outputs remain ignored by Git:

```text
kbs/audit/
```

## Acceptance Criteria

Gate 16B initial slice is complete when:

1. `python -m app.scripts.run_gate16b_auth_adapter_security_audit` completes successfully.
2. Local policy adapter authorizes `GATE15_AUTH_SMOKE` for claim mutation.
3. Local policy adapter denies `GATE15_OBSERVER_SMOKE` for gap mutation.
4. Local policy adapter denies `UNKNOWN_REVIEWER` before mutation.
5. Denied requests write security denial audit events.
6. Denial audit validates with `[gate16b:audit] OK`.
7. Audit events include finalization allowed set to false.
8. Audit hash chain validates from `GENESIS`.
9. No review mutation audit event is created for denied requests.
10. No production provider is implied or hard-coded.

## Non-Goals

Gate 16B does not:

- implement OIDC,
- implement reverse-proxy identity trust,
- implement signed service tokens,
- replace Gate 15 guarded endpoint,
- add browser mutation,
- finalize drafts,
- call an LLM.

## Recommended Next Gate

Recommended next gate:

**Gate 16C — Guarded Endpoint Uses Auth Adapter and Security Denial Audit**

Gate 16C should wire the Gate 15 guarded endpoint to the Gate 16B auth adapter and security denial audit writer so denied endpoint requests produce security audit events consistently.

Proposed sequence:

1. Refactor guarded endpoint authorization to call `LocalPolicyAuthAdapter`.
2. On `PermissionError`/authorization denial, append security denial audit event.
3. Preserve existing Gate 15 behavior for authorized mutation.
4. Extend smoke runner to validate denial audit output from endpoint-level denials.
5. Keep finalization disabled.

Do not add browser mutation until endpoint-level security denial auditing is wired.

## Notes

Gate 16B creates the seam and the denial log. The endpoint does not use it yet. That is Gate 16C. Apparently even the doorman needs an audit notebook now. This is probably wise, and therefore annoying.
