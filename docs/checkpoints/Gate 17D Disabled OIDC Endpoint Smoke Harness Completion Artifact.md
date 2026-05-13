# Gate 17D Disabled OIDC Endpoint Smoke Harness Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: Disabled OIDC Smoke Harness and Security-Denial Audit Validation  
Status: Complete for current disabled smoke slice  
Generated: 2026-05-13

## Purpose

Gate 17D verifies that OIDC diagnostics can be exercised in a disabled smoke harness, mapped through the Gate 17C denial reason catalog, written into security-denial audit events, and validated without changing the live guarded endpoint.

Gate 17D does not accept OIDC tokens, does not replace `LocalPolicyAuthAdapter`, does not change the guarded endpoint, and does not enable finalization.

## Source Baseline

Gate 17D starts from Gate 17C:

- OIDC diagnostic failure codes exist.
- OIDC denial reason mapping exists.
- Mapped denial reasons validate in the existing security-denial audit schema.
- OIDC auth remains fail-closed.
- `LocalPolicyAuthAdapter` remains active for the guarded endpoint.
- Finalization remains disabled.

## Key Files Added

| File | Purpose |
|---|---|
| `backend/app/scripts/disabled_oidc_smoke_harness.py` | Disabled smoke harness that diagnoses OIDC failures and writes mapped security-denial audit events |
| `backend/app/scripts/validate_disabled_oidc_smoke_harness.py` | Validates smoke scenarios, mapped denial reasons, non-authorization, and audit compatibility |
| `backend/app/scripts/run_gate17d_disabled_oidc_smoke_harness.py` | Gate 17D validation runner |
| `docs/checkpoints/Gate 17D Disabled OIDC Endpoint Smoke Harness Build Plan.md` | Build plan and acceptance criteria |

## Pipeline

Run from `backend`:

```bash
python -m app.scripts.run_gate17d_disabled_oidc_smoke_harness
```

Dry run:

```bash
python -m app.scripts.run_gate17d_disabled_oidc_smoke_harness --dry-run
```

The runner verifies source files, runs `app.scripts.validate_disabled_oidc_smoke_harness`, and confirms disabled OIDC smoke failures write valid security-denial audit events without authorizing requests.

## Local Validation Status

Local validation completed successfully with:

```text
[gate17d:oidc-smoke] OK
[gate17d:oidc-smoke] scenarios=3
[gate17d:oidc-smoke] denial_reasons=mapped
[gate17d:oidc-smoke] security_audit=valid
[gate17d:oidc-smoke] authorization=unchanged_disabled
```

## Validation Coverage

Gate 17D validates three disabled smoke scenarios:

| Scenario | Expected failure code |
|---|---|
| Missing bearer auth header | `OIDC_TOKEN_MISSING` |
| Malformed bearer auth header | `OIDC_TOKEN_MALFORMED_AUTHORIZATION_HEADER` |
| Malformed JWT | `OIDC_TOKEN_MALFORMED_JWT` |

For each scenario, the harness maps the diagnostic failure through the Gate 17C denial reason catalog and appends a temporary security-denial audit event. The validator then reuses the existing security-denial audit validator to confirm the temporary audit file is valid.

## What This Proves

Gate 17D proves that the project can now:

- exercise OIDC diagnostics in a disabled smoke path,
- map OIDC diagnostic failures to audit-safe denial reasons,
- write mapped failures into valid security-denial audit events,
- validate the resulting audit chain,
- avoid persistent smoke artifacts,
- keep the real guarded endpoint unchanged,
- keep `LocalPolicyAuthAdapter` active,
- keep finalization disabled.

## Known Limitations

Gate 17D remains disabled-smoke-only.

It does not implement production OIDC validation, JWKS validation, token claim mapping, endpoint integration, or finalization.

## Recommended Next Gate

Recommended next gate:

**Gate 17E — OIDC JWKS Validation Design Spec**

Gate 17E should specify deterministic production token validation before implementation, including issuer/audience requirements, JWKS retrieval and caching policy, accepted algorithms, clock-skew policy, claim-to-reviewer mapping, denial-audit integration, and explicit enablement guardrails.

## Completion Status

Gate 17D is complete for the current disabled OIDC smoke harness slice.

The next work should begin from this checkpoint, not from memory.
