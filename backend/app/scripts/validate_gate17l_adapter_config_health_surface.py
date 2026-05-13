from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.guarded_review_update_http_server import adapter_config_health_payload


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_missing_config_reports_local_policy_default() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        payload = adapter_config_health_payload(Path(temp_dir) / "missing.json")
        if payload["configured_adapter"] != "local_policy":
            raise AssertionError(f"Expected local_policy default, got: {payload}")
        if payload["allow_oidc_adapter"] is not False:
            raise AssertionError(f"Expected OIDC disabled by default, got: {payload}")
        if payload["status"] != "OK":
            raise AssertionError(f"Expected missing config to report safe OK default, got: {payload}")
        if payload["endpoint_integration_allowed"] is not False:
            raise AssertionError(f"Health surface must not allow endpoint integration, got: {payload}")
        if payload["live_adapter"] != "local_policy":
            raise AssertionError(f"Live adapter must remain local_policy, got: {payload}")
        if payload["read_only_health_surface"] is not True:
            raise AssertionError(f"Expected read-only marker, got: {payload}")


def assert_invalid_config_reports_errors_without_switching_live_adapter() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "invalid.json"
        write_json(path, {"review_update_auth_adapter": "oidc", "allow_oidc_adapter": False})
        payload = adapter_config_health_payload(path)
        if payload["configured_adapter"] != "oidc":
            raise AssertionError(f"Expected configured adapter oidc, got: {payload}")
        if payload["status"] != "ERROR":
            raise AssertionError(f"Expected invalid config status ERROR, got: {payload}")
        if not payload["errors"]:
            raise AssertionError(f"Expected validation errors, got: {payload}")
        if payload["endpoint_integration_allowed"] is not False:
            raise AssertionError(f"Invalid config must not allow integration, got: {payload}")
        if payload["live_adapter"] != "local_policy":
            raise AssertionError(f"Live adapter must remain local_policy, got: {payload}")


def assert_explicit_allowed_oidc_reports_structural_ok_but_health_only() -> None:
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
        payload = adapter_config_health_payload(path)
        if payload["status"] != "OK":
            raise AssertionError(f"Expected structural config OK, got: {payload}")
        if payload["configured_adapter"] != "oidc":
            raise AssertionError(f"Expected configured adapter oidc, got: {payload}")
        if payload["endpoint_integration_allowed"] is not False:
            raise AssertionError(f"Gate 17L must remain health-only, got: {payload}")
        if payload["live_adapter"] != "local_policy":
            raise AssertionError(f"Live adapter must remain local_policy, got: {payload}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 17L adapter config read-only health surface.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_missing_config_reports_local_policy_default()
    assert_invalid_config_reports_errors_without_switching_live_adapter()
    assert_explicit_allowed_oidc_reports_structural_ok_but_health_only()
    print("[gate17l:health] OK")
    print("[gate17l:health] missing_config=local_policy_default")
    print("[gate17l:health] invalid_config=reported")
    print("[gate17l:health] configured_oidc=health_only")
    print("[gate17l:health] live_adapter=local_policy")


if __name__ == "__main__":
    main()
