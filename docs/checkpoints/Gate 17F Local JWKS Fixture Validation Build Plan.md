# Gate 17F Local JWKS Fixture Validation Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Local JWKS Fixture Structure and Key Selection Validation  
Status: Proposed / initial patches applied  
Generated: 2026-05-13

## Purpose

Gate 17F answers this bounded question:

> Can the project validate local JWKS fixture structure and select keys by `kid` without network retrieval, endpoint wiring, production token acceptance, or signature validation?

The intended answer is yes.

Gate 17F implements local-file-only JWKS fixture helpers. It remains structural and non-authorizing.

## Source Baseline

Gate 17F starts from Gate 17E:

- OIDC/JWKS validation design spec exists.
- OIDC adapter remains fail-closed.
- OIDC diagnostics remain non-authorizing.
- Guarded endpoint remains on `LocalPolicyAuthAdapter`.
- Finalization remains disabled.

## Scope

In scope:

1. Load local JWKS fixture JSON from disk.
2. Validate `keys` list exists and is non-empty.
3. Validate RSA signing key shape for local fixtures.
4. Require `kid` by default.
5. Reject duplicate `kid` values.
6. Reject unsupported algorithms.
7. Select a local key by `kid`.
8. Keep all helper outputs non-authorizing.
9. Add temporary-file validation coverage.

Out of scope:

- network JWKS retrieval,
- JWT signature validation,
- accepting production tokens,
- endpoint wiring,
- replacing `LocalPolicyAuthAdapter`,
- committing persistent fixture artifacts,
- finalization.

## Initial Patches

| File | Purpose |
|---|---|
| `backend/app/scripts/local_jwks_fixture_validator.py` | Local JWKS fixture loader, structure validator, and key selector |
| `backend/app/scripts/validate_local_jwks_fixture_validator.py` | Temporary-file validation coverage for valid and invalid fixture cases |
| `backend/app/scripts/run_gate17f_local_jwks_fixture_validation.py` | Gate 17F validation runner |

## Validation Cases

Gate 17F validates:

- valid local RSA JWKS fixture succeeds structurally,
- key selection by known `kid` succeeds structurally,
- missing `kid` fails closed,
- duplicate `kid` fails closed,
- unsupported algorithm fails closed,
- unknown `kid` fails closed,
- all results remain `authorization_allowed = false`.

## Proposed Validation Commands

From `backend`:

```bash
python -m app.scripts.run_gate17f_local_jwks_fixture_validation
```

Dry run:

```bash
python -m app.scripts.run_gate17f_local_jwks_fixture_validation --dry-run
```

Expected output:

```text
[gate17f:jwks-fixture] OK
[gate17f:jwks-fixture] local_fixture_structure=valid
[gate17f:jwks-fixture] key_selection=valid
[gate17f:jwks-fixture] invalid_fixture=fail_closed
[gate17f:jwks-fixture] authorization=unchanged_disabled
```

## Acceptance Criteria

Gate 17F is complete when:

- local JWKS fixture validator accepts valid fixture structure,
- local JWKS key selector selects a fixture key by `kid`,
- invalid fixtures fail closed,
- unknown key selection fails closed,
- no network retrieval is implemented,
- no signature validation is claimed,
- no endpoint wiring occurs,
- `LocalPolicyAuthAdapter` remains active,
- finalization remains disabled.

## Recommended Follow-On

After Gate 17F validates, the next gate can be:

**Gate 17G — Deterministic JWT Signature Validation Against Fixture JWKS**

Gate 17G should validate a fixture JWT signature against a local fixture JWKS only. It should still avoid network JWKS retrieval and endpoint wiring.
