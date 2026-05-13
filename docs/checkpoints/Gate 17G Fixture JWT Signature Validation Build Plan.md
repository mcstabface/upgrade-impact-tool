# Gate 17G Fixture JWT Signature Validation Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Deterministic JWT Signature Validation Against Fixture JWKS  
Status: Proposed / initial patches applied  
Generated: 2026-05-13

## Purpose

Gate 17G answers this bounded question:

> Can the project validate a fixture RS256 JWT signature against a local fixture JWKS without network retrieval, endpoint wiring, production token acceptance, or adapter replacement?

The intended answer is yes.

Gate 17G implements local fixture JWT signature validation only. It remains non-authorizing.

## Source Baseline

Gate 17G starts from Gate 17F:

- local JWKS fixture validation exists,
- local key selection by `kid` exists,
- fixture helpers remain non-authorizing,
- guarded endpoint remains on `LocalPolicyAuthAdapter`,
- finalization remains disabled.

## Scope

In scope:

1. Parse fixture JWT header and payload.
2. Select local fixture JWK by `kid`.
3. Validate RS256 signature using standard-library primitives.
4. Reject tampered payloads.
5. Reject unknown `kid` values.
6. Reject unsupported algorithms.
7. Keep validation result non-authorizing.
8. Add temporary-file validation coverage.

Out of scope:

- network JWKS retrieval,
- production token acceptance,
- endpoint wiring,
- claim authorization,
- reviewer mapping,
- replacing `LocalPolicyAuthAdapter`,
- finalization.

## Initial Patches

| File | Purpose |
|---|---|
| `backend/app/scripts/fixture_jwt_signature_validator.py` | Local fixture JWT signature validator |
| `backend/app/scripts/validate_fixture_jwt_signature_validator.py` | Fixture validation tests |
| `backend/app/scripts/run_gate17g_fixture_jwt_signature_validation.py` | Gate 17G validation runner |

## Validation Cases

Gate 17G validates:

- valid fixture JWT signature succeeds,
- tampered payload fails closed,
- unknown `kid` fails closed,
- unsupported algorithm fails closed,
- all results remain `authorization_allowed = false`.

## Proposed Validation Commands

From `backend`:

```bash
python -m app.scripts.run_gate17g_fixture_jwt_signature_validation
```

Dry run:

```bash
python -m app.scripts.run_gate17g_fixture_jwt_signature_validation --dry-run
```

Expected output:

```text
[gate17g:jwt-fixture] OK
[gate17g:jwt-fixture] signature=valid
[gate17g:jwt-fixture] tampered_payload=fail_closed
[gate17g:jwt-fixture] unknown_kid=fail_closed
[gate17g:jwt-fixture] unsupported_alg=fail_closed
[gate17g:jwt-fixture] authorization=unchanged_disabled
```

## Acceptance Criteria

Gate 17G is complete when:

- fixture JWT signature validates against local fixture JWK,
- tampered JWT fails closed,
- unknown key ID fails closed,
- unsupported algorithm fails closed,
- no network retrieval is implemented,
- no production token acceptance is claimed,
- no endpoint wiring occurs,
- `LocalPolicyAuthAdapter` remains active,
- finalization remains disabled.

## Recommended Follow-On

After Gate 17G validates, the next gate can be:

**Gate 17H — Fixture Claim Validation and Reviewer Mapping**

Gate 17H should validate issuer, audience, and fixture reviewer claims after fixture signature validation, still without endpoint wiring or production token acceptance.
