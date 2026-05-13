from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.fixture_jwt_signature_validator import validate_fixture_jwt_signature


FIXTURE_JWK = {
    "kty": "RSA",
    "use": "sig",
    "alg": "RS256",
    "kid": "gate17g-fixture-key-001",
    "n": "l9eYjq89mJyf9MgAD3rv2dPxVzf4TmDVU174HOy4Rsp4iOTmdBhhoF-FBdxFruNLt19clCo47mE-MC95LftwBcDrqaX2dzoIHDF5utAggv7eb0EPfGeTdLvrX-pQycvYtHZrBmA-xVjGRXydK1gCVVr89XeeeKXi-qGFL-DOWe8",
    "e": "AQAB",
}

FIXTURE_JWT = "eyJhbGciOiJSUzI1NiIsImtpZCI6ImdhdGUxN2ctZml4dHVyZS1rZXktMDAxIiwidHlwIjoiSldUIn0.eyJhdWQiOiJ1cGdyYWRlLWltcGFjdC10b29sIiwiaXNzIjoiaHR0cHM6Ly9pc3N1ZXIuZXhhbXBsZS50ZXN0IiwicHJlZmVycmVkX3VzZXJuYW1lIjoiR0FURTE3R19GSVhUVVJFIn0.NNM4iOPtqByuJP50Ai2RaJJ-JjFU6XfdIMUk9-HIFyP3lGbJnQ454b65C3u8M9sD1tlVypA-nJLYxCGV4zPpFFDv_vMYR5ACMvQkHIlvZU4OkOvORLbYPhO3fjKWexCr17I08y6iHBRhnWpW-ehtcdA7VfgVvszu0DfKWZkGnis"


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def with_fixture_jwks() -> tuple[tempfile.TemporaryDirectory[str], Path]:
    temp_dir = tempfile.TemporaryDirectory()
    path = Path(temp_dir.name) / "fixture.jwks.json"
    write_json(path, {"keys": [FIXTURE_JWK]})
    return temp_dir, path


def assert_valid_fixture_signature_verifies() -> None:
    temp_dir, path = with_fixture_jwks()
    try:
        result = validate_fixture_jwt_signature(FIXTURE_JWT, jwks_path=path)
        if result.status != "OK":
            raise AssertionError(f"Expected fixture JWT signature OK, got: {result}")
        if result.authorization_allowed is not False:
            raise AssertionError("Fixture signature validation must not authorize.")
        if result.header.get("kid") != "gate17g-fixture-key-001":
            raise AssertionError(f"Expected fixture kid, got: {result.header}")
        if result.payload.get("preferred_username") != "GATE17G_FIXTURE":
            raise AssertionError(f"Expected fixture payload, got: {result.payload}")
    finally:
        temp_dir.cleanup()


def assert_tampered_payload_fails() -> None:
    temp_dir, path = with_fixture_jwks()
    try:
        parts = FIXTURE_JWT.split(".")
        tampered = f"{parts[0]}.eyJ0YW1wZXJlZCI6dHJ1ZX0.{parts[2]}"
        result = validate_fixture_jwt_signature(tampered, jwks_path=path)
        if result.status != "ERROR":
            raise AssertionError(f"Expected tampered JWT to fail, got: {result}")
        if "JWT_SIGNATURE_INVALID" not in [failure.code for failure in result.failures]:
            raise AssertionError(f"Expected JWT_SIGNATURE_INVALID, got: {result.failures}")
    finally:
        temp_dir.cleanup()


def assert_unknown_kid_fails() -> None:
    temp_dir, path = with_fixture_jwks()
    try:
        parts = FIXTURE_JWT.split(".")
        token_with_unknown_kid = "eyJhbGciOiJSUzI1NiIsImtpZCI6Im1pc3Npbmcta2V5IiwidHlwIjoiSldUIn0." + parts[1] + "." + parts[2]
        result = validate_fixture_jwt_signature(token_with_unknown_kid, jwks_path=path)
        if result.status != "ERROR":
            raise AssertionError(f"Expected unknown kid to fail, got: {result}")
        if "JWKS_KEY_NOT_FOUND" not in [failure.code for failure in result.failures]:
            raise AssertionError(f"Expected JWKS_KEY_NOT_FOUND, got: {result.failures}")
    finally:
        temp_dir.cleanup()


def assert_unsupported_alg_fails() -> None:
    temp_dir, path = with_fixture_jwks()
    try:
        parts = FIXTURE_JWT.split(".")
        token_with_bad_alg = "eyJhbGciOiJub25lIiwia2lkIjoiZ2F0ZTE3Zy1maXh0dXJlLWtleS0wMDEiLCJ0eXAiOiJKV1QifQ." + parts[1] + "." + parts[2]
        result = validate_fixture_jwt_signature(token_with_bad_alg, jwks_path=path)
        if result.status != "ERROR":
            raise AssertionError(f"Expected unsupported alg to fail, got: {result}")
        if "JWT_ALG_UNSUPPORTED" not in [failure.code for failure in result.failures]:
            raise AssertionError(f"Expected JWT_ALG_UNSUPPORTED, got: {result.failures}")
    finally:
        temp_dir.cleanup()


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 17G fixture JWT signature validator.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_valid_fixture_signature_verifies()
    assert_tampered_payload_fails()
    assert_unknown_kid_fails()
    assert_unsupported_alg_fails()
    print("[gate17g:jwt-fixture] OK")
    print("[gate17g:jwt-fixture] signature=valid")
    print("[gate17g:jwt-fixture] tampered_payload=fail_closed")
    print("[gate17g:jwt-fixture] unknown_kid=fail_closed")
    print("[gate17g:jwt-fixture] unsupported_alg=fail_closed")
    print("[gate17g:jwt-fixture] authorization=unchanged_disabled")


if __name__ == "__main__":
    main()
