from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.local_jwks_fixture_validator import select_local_jwk_by_kid, validate_local_jwks_fixture


VALID_RSA_JWK = {
    "kty": "RSA",
    "use": "sig",
    "alg": "RS256",
    "kid": "gate17f-fixture-key-001",
    "n": "sXchFixtureModulusValueOnlyForStructureChecks",
    "e": "AQAB",
}


def write_json(path: Path, payload: object) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_valid_fixture_is_structurally_ok() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "valid.jwks.json"
        write_json(path, {"keys": [VALID_RSA_JWK]})
        result = validate_local_jwks_fixture(path)
        if result.status != "OK":
            raise AssertionError(f"Expected valid fixture result OK, got: {result}")
        if result.authorization_allowed is not False:
            raise AssertionError("Local JWKS fixture validation must not authorize.")
        if result.kids != ["gate17f-fixture-key-001"]:
            raise AssertionError(f"Expected fixture kid list, got: {result.kids}")


def assert_key_selection_by_kid_is_structurally_ok() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "valid.jwks.json"
        write_json(path, {"keys": [VALID_RSA_JWK]})
        selected = select_local_jwk_by_kid(path, kid="gate17f-fixture-key-001")
        if selected.status != "OK":
            raise AssertionError(f"Expected key selection OK, got: {selected}")
        if selected.authorization_allowed is not False:
            raise AssertionError("Local JWK selection must not authorize.")
        if not selected.key or selected.key.get("kid") != "gate17f-fixture-key-001":
            raise AssertionError(f"Expected selected fixture key, got: {selected}")


def assert_missing_kid_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "missing_kid.jwks.json"
        key = dict(VALID_RSA_JWK)
        key.pop("kid")
        write_json(path, {"keys": [key]})
        result = validate_local_jwks_fixture(path)
        if result.status != "ERROR":
            raise AssertionError(f"Expected missing kid to fail, got: {result}")
        if "JWKS_KID_MISSING" not in [failure.code for failure in result.failures]:
            raise AssertionError(f"Expected JWKS_KID_MISSING, got: {result.failures}")


def assert_duplicate_kid_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "duplicate_kid.jwks.json"
        write_json(path, {"keys": [VALID_RSA_JWK, VALID_RSA_JWK]})
        result = validate_local_jwks_fixture(path)
        if result.status != "ERROR":
            raise AssertionError(f"Expected duplicate kid to fail, got: {result}")
        if "JWKS_KID_DUPLICATE" not in [failure.code for failure in result.failures]:
            raise AssertionError(f"Expected JWKS_KID_DUPLICATE, got: {result.failures}")


def assert_unsupported_algorithm_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "bad_alg.jwks.json"
        key = dict(VALID_RSA_JWK)
        key["alg"] = "none"
        write_json(path, {"keys": [key]})
        result = validate_local_jwks_fixture(path)
        if result.status != "ERROR":
            raise AssertionError(f"Expected unsupported alg to fail, got: {result}")
        if "JWKS_ALG_UNSUPPORTED" not in [failure.code for failure in result.failures]:
            raise AssertionError(f"Expected JWKS_ALG_UNSUPPORTED, got: {result.failures}")


def assert_unknown_kid_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "valid.jwks.json"
        write_json(path, {"keys": [VALID_RSA_JWK]})
        selected = select_local_jwk_by_kid(path, kid="missing-kid")
        if selected.status != "ERROR":
            raise AssertionError(f"Expected unknown kid selection to fail, got: {selected}")
        if selected.authorization_allowed is not False:
            raise AssertionError("Unknown kid selection must not authorize.")
        if "JWKS_KEY_NOT_FOUND" not in [failure.code for failure in selected.failures]:
            raise AssertionError(f"Expected JWKS_KEY_NOT_FOUND, got: {selected.failures}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 17F local JWKS fixture helper.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_valid_fixture_is_structurally_ok()
    assert_key_selection_by_kid_is_structurally_ok()
    assert_missing_kid_fails_closed()
    assert_duplicate_kid_fails_closed()
    assert_unsupported_algorithm_fails_closed()
    assert_unknown_kid_fails_closed()
    print("[gate17f:jwks-fixture] OK")
    print("[gate17f:jwks-fixture] local_fixture_structure=valid")
    print("[gate17f:jwks-fixture] key_selection=valid")
    print("[gate17f:jwks-fixture] invalid_fixture=fail_closed")
    print("[gate17f:jwks-fixture] authorization=unchanged_disabled")


if __name__ == "__main__":
    main()
