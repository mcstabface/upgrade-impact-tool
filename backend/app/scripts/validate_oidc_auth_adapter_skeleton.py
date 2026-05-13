from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.oidc_auth_adapter import OIDCAuthAdapter, load_oidc_auth_config


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_disabled_missing_config_fails_closed() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        missing_path = Path(temp_dir) / "missing_oidc_config.json"
        config = load_oidc_auth_config(missing_path)
        if config.enabled is not False:
            raise AssertionError("Missing OIDC config must load disabled config.")
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
        adapter = OIDCAuthAdapter(config_path)
        decision = adapter.authorize_request_context({"Authorization": "Bearer fake"}, action="claim")
        if decision.allowed is not False:
            raise AssertionError("Gate 17A OIDC skeleton must fail closed even with complete config.")
        if "not enabled for token validation" not in decision.reason:
            raise AssertionError(f"Unexpected complete-config denial reason: {decision.reason}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 17A inert OIDC auth adapter skeleton.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_disabled_missing_config_fails_closed()
    assert_enabled_incomplete_config_fails_closed()
    assert_complete_config_still_fails_closed()
    print("[gate17a:oidc] OK")
    print("[gate17a:oidc] missing_config=fail_closed")
    print("[gate17a:oidc] incomplete_enabled_config=fail_closed")
    print("[gate17a:oidc] complete_config_without_token_validation=fail_closed")


if __name__ == "__main__":
    main()
