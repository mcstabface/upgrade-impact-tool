# Gate 17C OIDC Security Denial Reason Mapping Build Plan

System: Upgrade Impact Analysis Tool  
Phase: OIDC Diagnostic Failure to Security-Denial Reason Mapping  
Status: Proposed / initial patches applied  
Generated: 2026-05-13

## Purpose

Gate 17C answers this bounded question:

> Can OIDC diagnostic failures be mapped into audit-safe security-denial reasons without accepting tokens, changing the security audit schema, wiring OIDC into the guarded endpoint, or replacing local-policy auth?

The intended answer is yes.

Gate 17C adds a deterministic denial reason taxonomy and validator. It keeps the existing `security_denial_audit.py` JSONL schema unchanged.

## Source Baseline

Gate 17C starts from Gate 17B:

- deterministic bearer extraction exists,
- unsafe JWT diagnostic parsing exists,
- config diagnostics exist,
- OIDC runtime auth remains fail-closed,
- OIDC is not wired into the guarded endpoint,
- `LocalPolicyAuthAdapter` remains active,
- finalization remains disabled.

## Scope

In scope:

1. Add OIDC denial reason catalog.
2. Add mapping from diagnostic failure codes to audit-safe denial reason strings.
3. Add audit-safe denial reason validator.
4. Validate unknown OIDC failure codes map to a safe fallback reason.
5. Validate mapped reasons can be written to the existing security-denial audit JSONL schema.
6. Reuse `validate_security_denial_audit.py` to prove compatibility.
7. Add Gate 17C runner.

Out of scope:

- endpoint OIDC wiring,
- accepting OIDC tokens,
- JWT signature validation,
- JWKS fetching/caching,
- issuer/audience/time-claim validation,
- changing the security-denial audit schema,
- changing `LocalPolicyAuthAdapter`,
- finalization.

## Initial Patches

| File | Purpose |
|---|---|
| `backend/app/scripts/oidc_denial_reasons.py` | OIDC denial reason taxonomy and mapping helpers |
| `backend/app/scripts/validate_oidc_denial_reason_mapping.py` | Validates taxonomy safety, diagnostic mapping, and security audit compatibility |
| `backend/app/scripts/run_gate17c_oidc_denial_reason_mapping.py` | Gate 17C validation runner |

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

## Proposed Validation Commands

From `backend`:

```bash
python -m app.scripts.run_gate17c_oidc_denial_reason_mapping
```

Dry run:

```bash
python -m app.scripts.run_gate17c_oidc_denial_reason_mapping --dry-run
```

Expected output:

```text
[gate17c:oidc-denial] OK
[gate17c:oidc-denial] catalog=audit_safe
[gate17c:oidc-denial] diagnostics=mapped
[gate17c:oidc-denial] security_audit=valid
[gate17c:oidc-denial] authorization=unchanged_fail_closed
```

## Acceptance Criteria

Gate 17C is complete when:

- every known OIDC diagnostic code maps to an audit-safe denial reason,
- unknown diagnostic code maps to safe fallback reason,
- mapped reasons contain no newlines/tabs and remain bounded length,
- mapped reasons can be appended to the existing security-denial audit schema,
- existing security-denial audit validator accepts mapped OIDC denial events,
- OIDC still does not authorize,
- guarded endpoint remains unchanged,
- `LocalPolicyAuthAdapter` remains active,
- finalization remains disabled.

## Recommended Follow-On

After Gate 17C validates, the next gate can be:

**Gate 17D — Disabled OIDC Endpoint Smoke Harness**

Gate 17D should add a disabled-only smoke harness that exercises the OIDC diagnostics and denial reason mapping as a separate test path, without replacing the active guarded endpoint adapter.

A later gate can then implement deterministic JWKS-backed signature validation behind explicit config.
