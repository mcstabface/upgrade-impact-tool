# Gate 17A OIDC Adapter Skeleton Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: Production Auth Skeleton Behind AuthAdapter Protocol  
Status: Complete for current inert skeleton slice  
Generated: 2026-05-13

## Purpose

This checkpoint captures the completed state of Gate 17A for the guarded review workflow.

Gate 17A answered this bounded question:

> Can the project add a production-auth-shaped OIDC adapter behind the existing `AuthAdapter` protocol without enabling it, weakening local policy auth, or allowing unaudited mutation?

For the current implementation slice, the answer is yes.

Gate 17A adds an inert OIDC adapter skeleton and validates fail-closed behavior. It does not enable OIDC authentication, does not replace the active `LocalPolicyAuthAdapter`, does not validate real tokens, and does not enable finalization.

## Source Baseline

Gate 17A starts from Gate 17 browser action scaffold and Gate 16B/Gate 16C auth seams.

Current baseline:

- Gate 11 review surface remains read-only.
- Gate 17 browser scaffold submits only through `POST /review/update`.
- guarded endpoint still uses `LocalPolicyAuthAdapter`.
- request provenance remains required.
- security-denial audit remains server-side.
- authorized mutation audit/provenance remains server-side.
- finalization remains disabled.
- `AuthAdapter` protocol exists.
- `AuthenticatedPrincipal`, `ReviewerIdentity`, and `AuthorizationDecision` dataclasses exist.

## Gate 17A Pipeline

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate17a_oidc_adapter_skeleton
```

Dry run:

```bash
python -m app.scripts.run_gate17a_oidc_adapter_skeleton --dry-run
```

The runner performs these steps:

1. verifies expected Gate 17A source files exist,
2. runs `app.scripts.validate_oidc_auth_adapter_skeleton`,
3. confirms the OIDC skeleton remains disabled and fail-closed.

## Key Files Added

| File | Purpose |
|---|---|
| `backend/app/scripts/oidc_auth_adapter.py` | Inert OIDC adapter skeleton and config contract |
| `backend/app/scripts/validate_oidc_auth_adapter_skeleton.py` | Fail-closed validation for missing, incomplete, and structurally complete configs |
| `backend/app/scripts/run_gate17a_oidc_adapter_skeleton.py` | Gate 17A validation runner |
| `docs/checkpoints/Gate 17A OIDC Adapter Skeleton Build Plan.md` | Build plan and acceptance criteria |

## OIDC Config Contract

Future config path:

```text
kbs/policies/review_oidc_adapter.config.json
```

Expected shape:

```json
{
  "enabled": false,
  "issuer": "https://issuer.example.test",
  "audience": "upgrade-impact-tool",
  "jwks_uri": "https://issuer.example.test/.well-known/jwks.json",
  "reviewer_id_claim": "preferred_username",
  "display_name_claim": "name",
  "email_claim": "email",
  "groups_claim": "groups",
  "role_claim": "roles",
  "required_groups": ["upgrade-impact-reviewers"]
}
```

No production config is committed in Gate 17A.

## Adapter Behavior

`OIDCAuthAdapter` implements the auth adapter method shape:

- `get_authenticated_principal(...)`
- `map_principal_to_reviewer(...)`
- `authorize_action(...)`
- `authorize_request_context(...)`

In Gate 17A, every runtime authorization path fails closed.

Fail-closed cases:

1. missing config,
2. enabled but incomplete config,
3. structurally complete config without token validation implementation.

This is intentional. The skeleton creates the seam without accepting any token.

## Local Validation Status

Local validation completed successfully with:

```text
[gate17a:oidc] OK
[gate17a:oidc] missing_config=fail_closed
[gate17a:oidc] incomplete_enabled_config=fail_closed
[gate17a:oidc] complete_config_without_token_validation=fail_closed
```

This proves:

- missing OIDC config loads disabled and denies,
- incomplete enabled config reports required-field problems and denies,
- complete structural config still denies because Gate 17A does not validate tokens.

## Validation Coverage

Gate 17A validates that:

- OIDC config loading is deterministic,
- missing config is safe,
- enabled incomplete config is unsafe and rejected,
- complete config does not accidentally authorize,
- no token is accepted by the skeleton,
- active guarded endpoint behavior remains unchanged because the endpoint is not wired to OIDC.

## What This Proves

Gate 17A proves that the project can now:

- represent a production-auth-shaped OIDC configuration,
- add an OIDC adapter behind the existing auth seam,
- preserve fail-closed behavior,
- keep local guarded endpoint behavior stable,
- avoid premature production-auth claims,
- keep finalization disabled.

## Known Limitations

Gate 17A remains a skeleton.

Known limitations:

- It does not parse JWTs.
- It does not validate JWT signatures.
- It does not fetch or cache JWKS.
- It does not validate issuer at runtime.
- It does not validate audience at runtime.
- It does not validate expiry or not-before claims.
- It does not map real token claims to reviewer identity.
- It does not replace `LocalPolicyAuthAdapter` in the guarded endpoint.
- It does not implement production web framework concerns.
- It does not add CSRF protection.
- It does not finalize drafts.
- It does not call an LLM.

These limitations are acceptable for Gate 17A. They define the next production-auth gate.

## Recommended Next Gate

Recommended next gate:

**Gate 17B — Deterministic Bearer Token Parsing and OIDC Config Validation**

Gate 17B should remain disabled by default while adding deterministic, test-only token parsing/config validation helpers. It should not accept production tokens until issuer/audience/JWKS validation is implemented.

Proposed Gate 17B sequence:

1. Add bearer-token extraction helper.
2. Add deterministic OIDC config validator CLI.
3. Add unsigned/test-token parsing only for fixture diagnostics, not authorization.
4. Add explicit failure audit reason taxonomy for OIDC-disabled, missing-token, malformed-token, invalid-config.
5. Keep `LocalPolicyAuthAdapter` as the active guarded endpoint adapter.
6. Keep finalization disabled.

Alternative next gate:

**Gate 18 — Review UI Action Scaffold Hardening**

If browser workflow remains the priority, Gate 18 can harden the Gate 17 scaffold with better operator validation and manual smoke documentation, without changing server auth.

## Completion Status

Gate 17A is complete for the current inert OIDC adapter skeleton slice.

The next work should begin from this checkpoint, not from memory.
