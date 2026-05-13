# Gate 17D Disabled OIDC Endpoint Smoke Harness Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Disabled OIDC Smoke Harness and Security-Denial Audit Validation  
Status: Proposed / initial patches applied  
Generated: 2026-05-13

## Purpose

Gate 17D answers this bounded question:

> Can the project exercise OIDC token/config diagnostics as a disabled smoke path, map failures through Gate 17C denial reasons, write valid security-denial audit events, and still avoid wiring OIDC into the guarded endpoint?

The intended answer is yes.

Gate 17D remains disabled and test-harness-only. It does not accept tokens and does not alter the live guarded endpoint.

## Source Baseline

Gate 17D starts from Gate 17C:

- OIDC diagnostic failure codes exist,
- OIDC denial reason mapping exists,
- mapped denial reasons validate in the existing security-denial audit schema,
- OIDC auth remains fail-closed,
- `LocalPolicyAuthAdapter` remains active for the guarded endpoint,
- finalization remains disabled.

## Scope

In scope:

1. Add a disabled OIDC smoke harness.
2. Exercise missing Authorization header, malformed Authorization header, and malformed JWT scenarios.
3. Map each diagnostic failure through Gate 17C denial reasons.
4. Write smoke failures to a temporary security-denial audit JSONL file.
5. Validate the temporary audit file with `validate_security_denial_audit.py`.
6. Prove smoke results remain non-authorizing.
7. Add Gate 17D runner.

Out of scope:

- changing `guarded_review_update_http_server.py`,
- replacing `LocalPolicyAuthAdapter`,
- accepting OIDC tokens,
- JWT signature validation,
- JWKS fetching/caching,
- issuer/audience/time-claim validation,
- reviewer mapping from token claims,
- persistent repository audit artifacts,
- finalization.

## Initial Patches

| File | Purpose |
|---|---|
| `backend/app/scripts/disabled_oidc_smoke_harness.py` | Disabled smoke harness that diagnoses OIDC failures and writes mapped security-denial audit events |
| `backend/app/scripts/validate_disabled_oidc_smoke_harness.py` | Validates harness scenarios, non-authorization, mapped reasons, and audit compatibility |
| `backend/app/scripts/run_gate17d_disabled_oidc_smoke_harness.py` | Gate 17D validation runner |

## Smoke Scenarios

Gate 17D includes three disabled smoke scenarios:

| Scenario | Expected failure code |
|---|---|
| missing Authorization header | `OIDC_TOKEN_MISSING` |
| malformed Authorization header | `OIDC_TOKEN_MALFORMED_AUTHORIZATION_HEADER` |
| malformed JWT | `OIDC_TOKEN_MALFORMED_JWT` |

Each scenario writes a security-denial audit event with:

```text
principal_issuer = oidc-disabled-smoke
source = gate17d-disabled-oidc-smoke
finalization_allowed = false
denial_reason = OIDC_DENIAL:<CATEGORY>:<MESSAGE>
```

## Proposed Validation Commands

From `backend`:

```bash
python -m app.scripts.run_gate17d_disabled_oidc_smoke_harness
```

Dry run:

```bash
python -m app.scripts.run_gate17d_disabled_oidc_smoke_harness --dry-run
```

Expected output:

```text
[gate17d:oidc-smoke] OK
[gate17d:oidc-smoke] scenarios=3
[gate17d:oidc-smoke] denial_reasons=mapped
[gate17d:oidc-smoke] security_audit=valid
[gate17d:oidc-smoke] authorization=unchanged_disabled
```

## Acceptance Criteria

Gate 17D is complete when:

- disabled smoke harness runs all three scenarios,
- expected OIDC diagnostic failure codes are produced,
- each failure maps to an audit-safe OIDC denial reason,
- temporary security-denial audit contains one event per scenario,
- existing security-denial audit validator accepts the temporary audit file,
- all smoke results report `authorization_allowed = false`,
- live guarded endpoint remains unchanged,
- `LocalPolicyAuthAdapter` remains active,
- finalization remains disabled.

## Recommended Follow-On

After Gate 17D validates, the next gate can be:

**Gate 17E — OIDC JWKS Validation Design Spec**

Gate 17E should specify deterministic production token validation before implementation:

1. issuer/audience requirements,
2. JWKS retrieval and caching policy,
3. accepted algorithms,
4. clock skew policy,
5. claim-to-reviewer mapping,
6. security-denial audit integration,
7. explicit enablement guardrails.

Implementation should wait until the design spec is complete. The poor auth stack deserves at least one page of adult supervision.
