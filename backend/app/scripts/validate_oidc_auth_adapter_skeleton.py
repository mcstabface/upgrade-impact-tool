from __future__ import annotations

import argparse
import base64
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.oidc_auth_adapter import (
    OIDCAuthAdapter,
    extract_bearer_token,
    load_oidc_auth_config,
    unsafe_parse_jwt_without_verification,
    validate_oidc_config_for_diagnostics,
)


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def b64url_json(payload: dict[str, Any]) -> str:
    encoded = base64.urlsafe_b64encode(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("utf-8")).decode("ascii")
    return encoded.rstrip("=")


def unsigned_fixture_jwt() -> str:
    return ".".join(
        [
            b64url_json({"alg": "none", "typ": "JWT"}),
            b64url_json({"iss": "https://issuer.example.test", "aud": "upgrade-impact-tool", "preferred_username": "GATE17B_FIXTURE"}),
            "fixture-signature-not-validated",
        ]
    )


def assert_disabled_missing_config_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        missing_path = Path(temp_dir) / "missing_oidc_config.json"
        config = load_oidc_auth_config(missing_path)
        if config.enabled is not False:
            raise AssertionError("Missing OIDC config must load disabled config.")
        diagnostic = validate_oidc_config_for_diagnostics(config)
        if diagnostic.status != "ERROR" or diagnostic.authorization_allowed is not False:
            raise AssertionError(f"Missing config diagnostic must fail closed: {diagnostic}")
        adapter = OIDCAuthAdapter(missing_path)
        decision = adapter.authorize_request_context({"Authorization": "Bearer fake"}, action="claim")
        if decision.allowed is not False:
            raise AssertionError("Missing OIDC config must fail closed.")
        if "disabled or missing config" not in decision.reason:
            raise AssertionError(f"Unexpected missing-config denial reason: {decision.reason}")


def assert_enabled_incomplete_config_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "incomplete_oidc_config.json"
        write_json(config_path, {"enabled": True, "issuer": "https://issuer.example.test"})
        config = load_oidc_auth_config(config_path)
        errors = config.validation_errors()
        if "enabled OIDC config requires audience" not in errors:
            raise AssertionError(f"Expected missing audience validation error, got: {errors}")
        if "enabled OIDC config requires jwks_uri" not in errors:
            raise AssertionError(f"Expected missing jwks_uri validation error, got: {errors}")
        diagnostic = validate_oidc_config_for_diagnostics(config)
        if diagnostic.status != "ERROR" or diagnostic.authorization_allowed is not False:
            raise AssertionError(f"Incomplete config diagnostic must fail closed: {diagnostic}")
        adapter = OIDCAuthAdapter(config_path)
        decision = adapter.authorize_request_context({"Authorization": "Bearer fake"}, action="claim")
        if decision.allowed is not False:
            raise AssertionError("Incomplete enabled OIDC config must fail closed.")
        if "config is invalid" not in decision.reason:
            raise AssertionError(f"Unexpected incomplete-config denial reason: {decision.reason}")


def assert_complete_config_still_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = Path(temp_dir) / "complete_oidc_config.json"
        write_json(
            config_path,
            {
                "enabled": True,
                "issuer": "https://issuer.example.test",
                "audience": "upgrade-impact-tool",
                "jwks_uri": "https://issuer.example.test/.well-known/jwks.json",
                "reviewer_id_claim": "preferred_username",
                "display_name_claim": "name",
                "email_claim": "email",
                "groups_claim": "groups",
                "role_claim": "roles",
                "required_groups": ["upgrade-impact-reviewers"],
            },
        )
        config = load_oidc_auth_config(config_path)
        errors = config.validation_errors()
        if errors:
            raise AssertionError(f"Complete OIDC skeleton config should validate structurally, got: {errors}")
        diagnostic = validate_oidc_config_for_diagnostics(config)
        if diagnostic.status != "OK" or diagnostic.authorization_allowed is not False:
            raise AssertionError(f"Complete config diagnostic must remain non-authorizing: {diagnostic}")
        adapter = OIDCAuthAdapter(config_path)
        decision = adapter.authorize_request_context({"Authorization": "Bearer fake"}, action="claim")
        if decision.allowed is not False:
            raise AssertionError("Gate 17B OIDC skeleton must fail closed even with complete config.")
        if "not enabled for token validation" not in decision.reason:
            raise AssertionError(f"Unexpected complete-config denial reason: {decision.reason}")


def assert_bearer_extraction_diagnostics() -> None:
    missing = extract_bearer_token({})
    if missing.status != "ERROR" or missing.failure_code != "OIDC_TOKEN_MISSING":
        raise AssertionError(f"Expected missing bearer diagnostic, got: {missing}")

    malformed = extract_bearer_token({"Authorization": "Basic abc"})
    if malformed.status != "ERROR" or malformed.failure_code != "OIDC_TOKEN_MALFORMED_AUTHORIZATION_HEADER":
        raise AssertionError(f"Expected malformed bearer diagnostic, got: {malformed}")

    valid = extract_bearer_token({"Authorization": "Bearer header.payload.signature"})
    if valid.status != "OK" or valid.token != "header.payload.signature":
        raise AssertionError(f"Expected bearer token extraction success, got: {valid}")


def assert_unsafe_jwt_diagnostics_do_not_authorize() -> None:
    malformed = unsafe_parse_jwt_without_verification("not-a-jwt")
    if malformed.status != "ERROR" or malformed.authorization_allowed is not False:
        raise AssertionError(f"Malformed JWT diagnostic must fail closed: {malformed}")

    parsed = unsafe_parse_jwt_without_verification(unsigned_fixture_jwt())
    if parsed.status != "OK":
        raise AssertionError(f"Expected fixture JWT to parse diagnostically, got: {parsed}")
    if parsed.authorization_allowed is not False:
        raise AssertionError("Unsafe JWT diagnostics must never authorize.")
    if parsed.header.get("alg") != "none":
        raise AssertionError(f"Expected fixture JWT header alg=none, got: {parsed.header}")
    if parsed.payload.get("preferred_username") != "GATE17B_FIXTURE":
        raise AssertionError(f"Expected fixture JWT payload username, got: {parsed.payload}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 17B inert OIDC auth adapter diagnostics.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_disabled_missing_config_fails_closed()
    assert_enabled_incomplete_config_fails_closed()
    assert_complete_config_still_fails_closed()
    assert_bearer_extraction_diagnostics()
    assert_unsafe_jwt_diagnostics_do_not_authorize()
    print("[gate17b:oidc] OK")
    print("[gate17b:oidc] missing_config=fail_closed")
    print("[gate17b:oidc] incomplete_enabled_config=fail_closed")
    print("[gate17b:oidc] complete_config_without_token_validation=fail_closed")
    print("[gate17b:oidc] bearer_extraction=diagnostic_only")
    print("[gate17b:oidc] unsafe_jwt_parse=non_authorizing")


if __name__ == "__main__":
    main()
