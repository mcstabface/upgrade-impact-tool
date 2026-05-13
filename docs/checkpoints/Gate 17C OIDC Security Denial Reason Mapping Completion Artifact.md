# Gate 17C OIDC Security Denial Reason Mapping Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: OIDC Diagnostic Failure to Security-Denial Reason Mapping  
Status: Complete for current mapping slice  
Generated: 2026-05-13

## Purpose

This checkpoint captures the completed state of Gate 17C for the guarded review workflow.

Gate 17C answered this bounded question:

> Can OIDC diagnostic failures be mapped into audit-safe security-denial reasons without accepting tokens, changing the security audit schema, wiring OIDC into the guarded endpoint, or replacing local-policy auth?

For the current implementation slice, the answer is yes.

Gate 17C adds a deterministic denial reason taxonomy and validator. It keeps the existing `security_denial_audit.py` JSONL schema unchanged.

## Source Baseline

Gate 17C starts from Gate 17B:

- deterministic bearer extraction exists,
- unsafe JWT diagnostic parsing exists,
- OIDC config diagnostics exist,
- OIDC runtime auth remains fail-closed,
- OIDC is not wired into the guarded endpoint,
- `LocalPolicyAuthAdapter` remains active,
- finalization remains disabled.

## Gate 17C Pipeline

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate17c_oidc_denial_reason_mapping
```

Dry run:

```bash
python -m app.scripts.run_gate17c_oidc_denial_reason_mapping --dry-run
```

The runner performs these steps:

1. verifies expected Gate 17C source files exist,
2. runs `app.scripts.validate_oidc_denial_reason_mapping`,
3. confirms OIDC diagnostic failures map to audit-safe denial reasons without authorizing requests.

## Key Files Added

| File | Purpose |
|---|---|
| `backend/app/scripts/oidc_denial_reasons.py` | OIDC denial reason taxonomy and mapping helpers |
| `backend/app/scripts/validate_oidc_denial_reason_mapping.py` | Validates taxonomy safety, diagnostic mapping, and security audit compatibility |
| `backend/app/scripts/run_gate17c_oidc_denial_reason_mapping.py` | Gate 17C validation runner |
| `docs/checkpoints/Gate 17C OIDC Security Denial Reason Mapping Build Plan.md` | Build plan and acceptance criteria |

## Denial Reason Format

Mapped OIDC denial reasons use this format:

```text
OIDC_DENIAL:<CATEGORY>:<AUDIT_SAFE_MESSAGE>
```

Examples:

```text
OIDC_DENIAL:TOKEN_MISSING:Authorization bearer token is required.
OIDC_DENIAL:TOKEN_MALFORMED_JWT:Bearer token is not a three-segment JWT.
OIDC_DENIAL:CONFIG_INVALID:OIDC adapter configuration is invalid.
```

These strings fit into the existing `denial_reason` field in `SecurityDenialAuditEvent`.

## Diagnostic Codes Covered

Gate 17C maps:

```text
OIDC_CONFIG_DISABLED
OIDC_CONFIG_INVALID
OIDC_TOKEN_MISSING
OIDC_TOKEN_MALFORMED_AUTHORIZATION_HEADER
OIDC_TOKEN_EMPTY
OIDC_TOKEN_MALFORMED_JWT
OIDC_TOKEN_UNSAFE_PARSE_FAILED
OIDC_TOKEN_VALIDATION_NOT_IMPLEMENTED
OIDC_REVIEWER_MAPPING_NOT_IMPLEMENTED
OIDC_ACTION_AUTHORIZATION_NOT_IMPLEMENTED
```

Unknown diagnostic codes map to:

```text
OIDC_DENIAL:UNKNOWN_FAILURE:OIDC failure code is not recognized.
```

## Security Audit Compatibility

Gate 17C intentionally does not change the `SecurityDenialAuditEvent` schema.

The validator writes mapped OIDC denial reasons into ordinary security-denial audit events and reuses:

```text
app.scripts.validate_security_denial_audit
```

This proves mapped OIDC reasons are compatible with the existing hash-chained security audit JSONL format.

## Local Validation Status

Local validation completed successfully with:

```text
[gate17c:oidc-denial] OK
[gate17c:oidc-denial] catalog=audit_safe
[gate17c:oidc-denial] diagnostics=mapped
[gate17c:oidc-denial] security_audit=valid
[gate17c:oidc-denial] authorization=unchanged_fail_closed
[gate17c] Pipeline complete
[gate17c] OIDC diagnostic failures map to audit-safe denial reasons without authorizing requests
```

This proves:

- every known OIDC diagnostic code maps to an audit-safe denial reason,
- unknown diagnostic codes map to an audit-safe fallback,
- mapped reasons contain no newlines/tabs and remain bounded length,
- mapped reasons validate inside existing security-denial audit events,
- existing security-denial audit hash-chain validation still passes,
- no authorization behavior changed.

## Validation Coverage

Gate 17C validates that:

- the OIDC denial reason catalog is complete for known Gate 17B diagnostic codes,
- mapped denial reasons are audit-safe,
- unknown diagnostic codes map safely,
- OIDC token/config diagnostics can be converted to denial reasons,
- mapped denial reasons can be appended to security-denial audit events,
- existing security-denial audit validation accepts mapped OIDC denial events.

## What This Proves

Gate 17C proves that the project can now:

- normalize OIDC diagnostic failures into stable denial reason strings,
- preserve the existing security audit schema,
- prepare for future endpoint integration without accepting tokens,
- keep OIDC authorization fail-closed,
- keep `LocalPolicyAuthAdapter` active,
- keep finalization disabled.

## Known Limitations

Gate 17C remains mapping-only.

Known limitations:

- It does not wire OIDC diagnostics into the guarded endpoint.
- It does not accept OIDC tokens.
- It does not validate JWT signatures.
- It does not fetch or cache JWKS.
- It does not validate issuer for authorization.
- It does not validate audience for authorization.
- It does not validate expiry or not-before claims for authorization.
- It does not map token claims to reviewer identity.
- It does not replace `LocalPolicyAuthAdapter` in the guarded endpoint.
- It does not implement production web framework concerns.
- It does not add CSRF protection.
- It does not finalize drafts.
- It does not call an LLM.

These limitations are acceptable for Gate 17C. They define the next disabled endpoint-auth smoke gate.

## Recommended Next Gate

Recommended next gate:

**Gate 17D — Disabled OIDC Endpoint Smoke Harness**

Gate 17D should add a disabled-only smoke harness that exercises OIDC diagnostics and denial reason mapping as a separate test path, without replacing the active guarded endpoint adapter.

Proposed Gate 17D sequence:

1. Add a disabled OIDC smoke endpoint/service helper that consumes request context only in test harnesses.
2. Map diagnostic failures through Gate 17C denial reasons.
3. Write security-denial audit events for disabled OIDC smoke failures.
4. Validate those audit events using the existing security-denial audit validator.
5. Keep `LocalPolicyAuthAdapter` active for the real guarded endpoint.
6. Keep finalization disabled.

A later gate can then implement deterministic JWKS-backed signature validation behind explicit config.

## Completion Status

Gate 17C is complete for the current OIDC security-denial reason mapping slice.

The next work should begin from this checkpoint, not from memory.
