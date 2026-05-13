from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from app.scripts.endpoint_adapter_selection_config import (
    DEFAULT_REVIEW_UPDATE_AUTH_ADAPTER,
    load_endpoint_adapter_selection_config,
    validate_endpoint_adapter_selection_config,
)
from app.scripts.extract_kb_source_manifest import repo_root


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_missing_config_defaults_to_local_policy() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        config = load_endpoint_adapter_selection_config(Path(temp_dir) / "missing.json")
        diagnostic = validate_endpoint_adapter_selection_config(config)
        if diagnostic.status != "OK":
            raise AssertionError(f"Missing config should default safely, got: {diagnostic}")
        if config.review_update_auth_adapter != DEFAULT_REVIEW_UPDATE_AUTH_ADAPTER:
            raise AssertionError(f"Expected local_policy default, got: {config}")
        if config.allow_oidc_adapter is not False:
            raise AssertionError(f"Expected OIDC disallowed by default, got: {config}")
        if diagnostic.endpoint_integration_allowed is not False:
            raise AssertionError(f"Skeleton must not allow endpoint integration: {diagnostic}")


def assert_unknown_adapter_fails() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "unknown.json"
        write_json(path, {"review_update_auth_adapter": "not-real"})
        diagnostic = validate_endpoint_adapter_selection_config(load_endpoint_adapter_selection_config(path))
        if diagnostic.status != "ERROR":
            raise AssertionError(f"Unknown adapter should fail: {diagnostic}")
        if not any("unsupported review_update_auth_adapter" in error for error in diagnostic.errors):
            raise AssertionError(f"Expected unsupported adapter error: {diagnostic.errors}")


def assert_oidc_selected_without_allow_fails() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "oidc_without_allow.json"
        write_json(path, {"review_update_auth_adapter": "oidc", "allow_oidc_adapter": False})
        diagnostic = validate_endpoint_adapter_selection_config(load_endpoint_adapter_selection_config(path))
        if diagnostic.status != "ERROR":
            raise AssertionError(f"OIDC without allow flag should fail: {diagnostic}")
        if not any("allow_oidc_adapter is false" in error for error in diagnostic.errors):
            raise AssertionError(f"Expected allow flag error: {diagnostic.errors}")


def assert_oidc_selected_with_allow_validates_but_does_not_integrate() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "oidc_allowed.json"
        write_json(
            path,
            {
                "review_update_auth_adapter": "oidc",
                "allow_oidc_adapter": True,
                "oidc_config_path": "kbs/policies/review_oidc_adapter.config.json",
                "local_policy_path": "kbs/policies/review_authorization_policy.v1.json",
            },
        )
        diagnostic = validate_endpoint_adapter_selection_config(load_endpoint_adapter_selection_config(path))
        if diagnostic.status != "OK":
            raise AssertionError(f"Explicitly allowed OIDC config should validate structurally: {diagnostic}")
        if diagnostic.endpoint_integration_allowed is not False:
            raise AssertionError(f"Gate 17K must not allow endpoint integration: {diagnostic}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 17K endpoint adapter selection config skeleton.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_missing_config_defaults_to_local_policy()
    assert_unknown_adapter_fails()
    assert_oidc_selected_without_allow_fails()
    assert_oidc_selected_with_allow_validates_but_does_not_integrate()
    print("[gate17k:adapter-config] OK")
    print("[gate17k:adapter-config] missing_config=local_policy_default")
    print("[gate17k:adapter-config] unknown_adapter=fail_closed")
    print("[gate17k:adapter-config] oidc_without_allow=fail_closed")
    print("[gate17k:adapter-config] endpoint_integration=not_enabled")


if __name__ == "__main__":
    main()
