# Gate 17B OIDC Token Config Validation Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Deterministic Bearer Token Parsing and OIDC Config Diagnostics  
Status: Proposed / initial patches applied  
Generated: 2026-05-13

## Purpose

Gate 17B answers this bounded question:

> Can the project add deterministic bearer-token extraction and OIDC config/token diagnostics without accepting tokens, wiring OIDC into the guarded endpoint, or weakening fail-closed behavior?

The intended answer is yes.

Gate 17B extends the inert Gate 17A OIDC skeleton with diagnostic helpers only. It still does not implement production OIDC auth.

## Source Baseline

Gate 17B starts from Gate 17A:

- `OIDCAuthAdapter` exists behind the auth adapter seam.
- missing config fails closed.
- incomplete enabled config fails closed.
- structurally complete config still fails closed.
- `LocalPolicyAuthAdapter` remains the active guarded endpoint adapter.
- finalization remains disabled.

## Scope

In scope:

1. Add deterministic bearer token extraction from request context.
2. Add explicit failure codes for missing, malformed, and empty bearer headers.
3. Add unsafe JWT header/payload parsing for fixture diagnostics only.
4. Ensure unsafe JWT parsing never authorizes.
5. Add OIDC config diagnostic result object.
6. Keep `OIDCAuthAdapter` fail-closed even with structurally complete config.
7. Add validation coverage for all diagnostic helper behavior.
8. Add Gate 17B runner.

Out of scope:

- JWT signature validation.
- issuer validation for authorization.
- audience validation for authorization.
- expiry / not-before validation for authorization.
- JWKS fetching or caching.
- reviewer mapping from real token claims.
- replacing `LocalPolicyAuthAdapter`.
- endpoint wiring.
- production session management.
- finalization.

## Initial Patches

| File | Purpose |
|---|---|
| `backend/app/scripts/oidc_auth_adapter.py` | Adds bearer extraction, unsafe JWT diagnostic parsing, and config diagnostics |
| `backend/app/scripts/validate_oidc_auth_adapter_skeleton.py` | Extends validation to Gate 17B diagnostic-only behavior |
| `backend/app/scripts/run_gate17b_oidc_token_config_validation.py` | Runs Gate 17B validation pipeline |

## Diagnostic Failure Codes

Gate 17B introduces these diagnostic-only failure codes:

```text
OIDC_TOKEN_MISSING
OIDC_TOKEN_MALFORMED_AUTHORIZATION_HEADER
OIDC_TOKEN_EMPTY
OIDC_TOKEN_MALFORMED_JWT
OIDC_TOKEN_UNSAFE_PARSE_FAILED
```

These codes are not yet wired into endpoint security-denial audit events. A later endpoint integration gate can map these reasons into audit output.

## Security Guardrails

- Bearer extraction does not authorize.
- Unsafe JWT parsing does not authorize.
- Parsed JWT claims are diagnostics only.
- `authorization_allowed` is always false for unsafe JWT diagnostics.
- The adapter still fails closed for every runtime authorization path.
- No production token should be accepted in Gate 17B.
- No OIDC config is committed.
- The guarded endpoint remains unchanged.

## Proposed Validation Commands

From `backend`:

```bash
python -m app.scripts.run_gate17b_oidc_token_config_validation
```

Dry run:

```bash
python -m app.scripts.run_gate17b_oidc_token_config_validation --dry-run
```

Expected output:

```text
[gate17b:oidc] OK
[gate17b:oidc] missing_config=fail_closed
[gate17b:oidc] incomplete_enabled_config=fail_closed
[gate17b:oidc] complete_config_without_token_validation=fail_closed
[gate17b:oidc] bearer_extraction=diagnostic_only
[gate17b:oidc] unsafe_jwt_parse=non_authorizing
```

## Acceptance Criteria

Gate 17B is complete when:

- missing Authorization header reports `OIDC_TOKEN_MISSING`,
- malformed Authorization header reports `OIDC_TOKEN_MALFORMED_AUTHORIZATION_HEADER`,
- valid-looking Bearer header extracts a token but does not authorize,
- malformed JWT reports `OIDC_TOKEN_MALFORMED_JWT`,
- fixture JWT header/payload parse succeeds for diagnostics,
- fixture JWT diagnostic reports `authorization_allowed = false`,
- complete OIDC config remains non-authorizing,
- `LocalPolicyAuthAdapter` remains active for the guarded endpoint,
- finalization remains disabled.

## Recommended Follow-On

After Gate 17B validates, the next production-auth gate can be:

**Gate 17C — OIDC Security Denial Reason Mapping**

That gate should map OIDC diagnostic failures into the security-denial audit taxonomy without accepting tokens and without replacing local-policy auth.

A later gate, only after that, can implement deterministic JWKS-backed signature validation behind explicit config.
