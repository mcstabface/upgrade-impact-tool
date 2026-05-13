# Gate 17B OIDC Token Config Validation Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: Deterministic Bearer Token Parsing and OIDC Config Diagnostics  
Status: Complete for current diagnostic-only slice  
Generated: 2026-05-13

## Purpose

This checkpoint captures the completed state of Gate 17B for the guarded review workflow.

Gate 17B answered this bounded question:

> Can the project add deterministic bearer-token extraction and OIDC config/token diagnostics without accepting tokens, wiring OIDC into the guarded endpoint, or weakening fail-closed behavior?

For the current implementation slice, the answer is yes.

Gate 17B extends the inert Gate 17A OIDC skeleton with diagnostic-only helpers. It does not accept production tokens, does not validate signatures, does not fetch JWKS, does not wire OIDC into the guarded endpoint, and does not enable finalization.

## Source Baseline

Gate 17B starts from Gate 17A:

- `OIDCAuthAdapter` exists behind the auth adapter seam.
- missing config fails closed.
- incomplete enabled config fails closed.
- structurally complete config still fails closed.
- `LocalPolicyAuthAdapter` remains the active guarded endpoint adapter.
- finalization remains disabled.

## Gate 17B Pipeline

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate17b_oidc_token_config_validation
```

Dry run:

```bash
python -m app.scripts.run_gate17b_oidc_token_config_validation --dry-run
```

The runner performs these steps:

1. verifies expected Gate 17B source files exist,
2. runs `app.scripts.validate_oidc_auth_adapter_skeleton`,
3. confirms bearer token parsing and JWT parsing remain diagnostic-only and non-authorizing.

## Key Files Added or Updated

| File | Purpose |
|---|---|
| `backend/app/scripts/oidc_auth_adapter.py` | Adds deterministic bearer extraction, unsafe JWT diagnostic parsing, and config diagnostics |
| `backend/app/scripts/validate_oidc_auth_adapter_skeleton.py` | Extends OIDC validation to Gate 17B diagnostics |
| `backend/app/scripts/run_gate17b_oidc_token_config_validation.py` | Gate 17B validation runner |
| `docs/checkpoints/Gate 17B OIDC Token Config Validation Build Plan.md` | Build plan and acceptance criteria |

## Diagnostic Helpers

Gate 17B adds:

- `extract_bearer_token(...)`
- `unsafe_parse_jwt_without_verification(...)`
- `validate_oidc_config_for_diagnostics(...)`
- diagnostic dataclasses for bearer extraction, unsafe JWT parsing, and config checks.

These helpers are deterministic and diagnostic-only.

## Diagnostic Failure Codes

Gate 17B introduces:

```text
OIDC_TOKEN_MISSING
OIDC_TOKEN_MALFORMED_AUTHORIZATION_HEADER
OIDC_TOKEN_EMPTY
OIDC_TOKEN_MALFORMED_JWT
OIDC_TOKEN_UNSAFE_PARSE_FAILED
```

These codes are not yet wired into endpoint security-denial audit events. A later endpoint integration gate can map them into audit output.

## Security Guardrails

Gate 17B preserves these guardrails:

- bearer extraction does not authorize,
- unsafe JWT parsing does not authorize,
- parsed JWT claims are diagnostics only,
- `authorization_allowed` is always false for unsafe JWT diagnostics,
- complete OIDC config still does not authorize,
- `OIDCAuthAdapter` still fails closed for every runtime authorization path,
- no production token is accepted,
- no OIDC config is committed,
- the guarded endpoint remains unchanged,
- `LocalPolicyAuthAdapter` remains active for guarded endpoint smoke tests,
- finalization remains disabled.

## Local Validation Status

Local validation completed successfully with:

```text
[gate17b:oidc] OK
[gate17b:oidc] missing_config=fail_closed
[gate17b:oidc] incomplete_enabled_config=fail_closed
[gate17b:oidc] complete_config_without_token_validation=fail_closed
[gate17b:oidc] bearer_extraction=diagnostic_only
[gate17b:oidc] unsafe_jwt_parse=non_authorizing
[gate17b] Pipeline complete
[gate17b] Bearer token parsing and JWT parsing remain diagnostic-only and non-authorizing
```

This proves:

- missing Authorization header reports missing-token diagnostics,
- malformed Authorization header reports malformed-header diagnostics,
- valid-looking Bearer header extracts a token without authorization,
- malformed JWT reports malformed-JWT diagnostics,
- fixture JWT header/payload can parse for diagnostics,
- fixture JWT diagnostics remain non-authorizing,
- structurally complete OIDC config still does not authorize.

## Validation Coverage

Gate 17B validates that:

- missing config fails closed,
- incomplete enabled config fails closed,
- structurally complete config fails closed,
- bearer-token extraction is deterministic,
- bearer-token extraction exposes explicit failure codes,
- unsafe JWT diagnostic parsing is deterministic,
- unsafe JWT diagnostic parsing does not authorize,
- adapter runtime auth paths remain fail-closed.

## What This Proves

Gate 17B proves that the project can now:

- parse bearer auth headers deterministically for diagnostics,
- parse JWT header/payload fixtures without verification for diagnostics,
- expose explicit OIDC diagnostic failure codes,
- preserve fail-closed behavior,
- keep production auth disabled until real validation exists,
- avoid premature endpoint wiring.

## Known Limitations

Gate 17B remains diagnostic-only.

Known limitations:

- It does not validate JWT signatures.
- It does not fetch or cache JWKS.
- It does not validate issuer for authorization.
- It does not validate audience for authorization.
- It does not validate expiry or not-before claims for authorization.
- It does not map token claims to reviewer identity.
- It does not write OIDC-specific security-denial audit events.
- It does not replace `LocalPolicyAuthAdapter` in the guarded endpoint.
- It does not implement production web framework concerns.
- It does not add CSRF protection.
- It does not finalize drafts.
- It does not call an LLM.

These limitations are acceptable for Gate 17B. They define the next production-auth gate.

## Recommended Next Gate

Recommended next gate:

**Gate 17C — OIDC Security Denial Reason Mapping**

Gate 17C should map OIDC diagnostic failures into a security-denial reason taxonomy and validator without accepting tokens and without replacing local-policy auth.

Proposed Gate 17C sequence:

1. Add OIDC denial reason taxonomy.
2. Add conversion from diagnostic failure codes to audit-safe denial reasons.
3. Add validator coverage for OIDC denial reason mapping.
4. Keep endpoint unchanged or add disabled-only smoke path.
5. Keep `LocalPolicyAuthAdapter` active.
6. Keep finalization disabled.

A later gate, after reason mapping, can implement deterministic JWKS-backed signature validation behind explicit config.

## Completion Status

Gate 17B is complete for the current diagnostic-only OIDC token/config validation slice.

The next work should begin from this checkpoint, not from memory.
