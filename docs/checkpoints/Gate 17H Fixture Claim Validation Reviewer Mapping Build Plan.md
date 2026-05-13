# Gate 17H Fixture Claim Validation Reviewer Mapping Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Fixture Claim Validation and Reviewer Mapping  
Status: Proposed  
Generated: 2026-05-13

## Purpose

Gate 17H adds fixture claim checks and fixture reviewer mapping after Gate 17G fixture signature checks.

This gate remains local-only and non-authorizing. It does not change the guarded endpoint or the active local policy auth path.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/fixture_claim_reviewer_mapper.py` | Fixture claim checks and reviewer identity mapping |
| `backend/app/scripts/validate_fixture_claim_reviewer_mapper.py` | Validation cases |
| `backend/app/scripts/run_gate17h_fixture_claim_reviewer_mapping.py` | Gate runner |

## Scope

In scope:

- issuer check,
- audience check,
- `exp` and `nbf` checks,
- required group check,
- reviewer ID claim check,
- mapping to `AuthenticatedPrincipal`,
- mapping to `ReviewerIdentity`,
- non-authorizing result objects.

Out of scope:

- endpoint integration,
- action authorization,
- production token use,
- network key lookup,
- finalization.

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate17h_fixture_claim_reviewer_mapping
```

Expected output:

```text
[gate17h:claims] OK
[gate17h:claims] reviewer_mapping=valid
[gate17h:claims] issuer_audience=validated
[gate17h:claims] time_claims=validated
[gate17h:claims] required_groups=validated
[gate17h:claims] authorization=unchanged_disabled
```

## Completion Criteria

Gate 17H is complete when valid fixture claims map to reviewer identity, invalid fixture claims fail closed, and the live guarded endpoint remains unchanged.

Recommended next gate: **Gate 17I — Disabled Endpoint OIDC Adapter Selection Smoke**.
