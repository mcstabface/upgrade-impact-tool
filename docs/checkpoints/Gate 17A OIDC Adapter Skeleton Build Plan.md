# Gate 17A OIDC Adapter Skeleton Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Production Auth Skeleton Behind AuthAdapter Protocol  
Status: Proposed / initial patches applied  
Generated: 2026-05-13

## Purpose

Gate 17A answers this bounded question:

> Can the project add a production-auth-shaped OIDC adapter behind the existing `AuthAdapter` protocol without enabling it, weakening local policy auth, or allowing unaudited mutation?

The intended answer is yes.

Gate 17A is an inert skeleton only. It introduces the OIDC config contract and adapter class shape, validates fail-closed behavior, and leaves the guarded endpoint on the existing `LocalPolicyAuthAdapter` path.

## Source Baseline

Gate 17A starts from Gate 17 browser action scaffold:

- Gate 11 review surface remains read-only.
- Gate 17 browser scaffold submits only through `POST /review/update`.
- Guarded endpoint still enforces authorization and provenance server-side.
- Security-denial audit remains server-side.
- Finalization remains disabled.

Gate 17A also starts from Gate 16B/Gate 16C auth seams:

- `AuthAdapter` protocol exists.
- `AuthenticatedPrincipal`, `ReviewerIdentity`, and `AuthorizationDecision` dataclasses exist.
- `LocalPolicyAuthAdapter` remains the active adapter for local guarded endpoint smoke tests.

## Scope

In scope:

1. Add `OIDCAuthConfig` dataclass.
2. Add deterministic JSON config loader.
3. Add `OIDCAuthAdapter` class implementing the existing auth adapter method shape.
4. Fail closed when config is missing.
5. Fail closed when enabled config is incomplete.
6. Fail closed even when config is structurally complete, because token validation is not implemented in Gate 17A.
7. Add validation script proving the above cases.
8. Add runner script for the Gate 17A validation pipeline.

Out of scope:

- JWT parsing.
- JWT signature validation.
- JWKS fetching/caching.
- issuer/audience enforcement at runtime.
- reverse-proxy asserted identity.
- signed service tokens.
- replacing `LocalPolicyAuthAdapter` in the guarded endpoint.
- finalization.
- LLM-assisted review decisions.

## Initial Patches

| File | Purpose |
|---|---|
| `backend/app/scripts/oidc_auth_adapter.py` | Adds inert OIDC adapter skeleton and config contract |
| `backend/app/scripts/validate_oidc_auth_adapter_skeleton.py` | Validates fail-closed behavior for missing, incomplete, and structurally complete configs |
| `backend/app/scripts/run_gate17a_oidc_adapter_skeleton.py` | Runs the Gate 17A validation pipeline |

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

## Acceptance Criteria

Gate 17A is complete when:

- Missing OIDC config loads as disabled.
- Missing OIDC config fails closed.
- Enabled incomplete OIDC config reports missing required fields and fails closed.
- Enabled structurally complete OIDC config still fails closed because token validation is not implemented.
- `LocalPolicyAuthAdapter` remains the active guarded endpoint adapter.
- Gate 17 browser scaffold remains unchanged in behavior.
- Finalization remains disabled.

## Proposed Validation Commands

From `backend`:

```bash
python -m app.scripts.run_gate17a_oidc_adapter_skeleton
```

Dry run:

```bash
python -m app.scripts.run_gate17a_oidc_adapter_skeleton --dry-run
```

Expected output:

```text
[gate17a:oidc] OK
[gate17a:oidc] missing_config=fail_closed
[gate17a:oidc] incomplete_enabled_config=fail_closed
[gate17a:oidc] complete_config_without_token_validation=fail_closed
```

## Non-Negotiable Guardrails

- OIDC adapter must not be active by default.
- OIDC adapter must fail closed.
- Guarded endpoint must continue using `LocalPolicyAuthAdapter` unless a later gate explicitly changes that.
- No token should be accepted by the Gate 17A skeleton.
- No production secrets or tenant-specific config should be committed.
- Finalization must remain disabled.

## Recommended Follow-On

After Gate 17A completes, a later production-auth gate can add deterministic token validation:

1. Parse bearer token from request context.
2. Validate issuer and audience.
3. Validate signature against pinned JWKS cache.
4. Validate expiry and not-before times.
5. Map principal claims to reviewer identity.
6. Map reviewer identity to authorized roles.
7. Preserve security-denial audit behavior for all failures.

This later gate should remain disabled until config and deployment boundary are explicitly defined.
