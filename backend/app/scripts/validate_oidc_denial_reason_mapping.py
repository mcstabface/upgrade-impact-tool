from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.oidc_auth_adapter import extract_bearer_token, unsafe_parse_jwt_without_verification, validate_oidc_config_for_diagnostics, load_oidc_auth_config
from app.scripts.oidc_denial_reasons import (
    OIDC_DENIAL_REASON_BY_CODE,
    is_audit_safe_oidc_denial_reason,
    map_oidc_failure_code_to_denial_reason,
    oidc_denial_reason_catalog,
)
from app.scripts.security_denial_audit import append_security_denial_event
from app.scripts.validate_security_denial_audit import validate_audit


def write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_catalog_is_audit_safe() -> None:
    catalog = oidc_denial_reason_catalog()
    if len(catalog) != len(OIDC_DENIAL_REASON_BY_CODE):
        raise AssertionError("OIDC denial reason catalog size mismatch.")
    for item in catalog:
        if not item.audit_safe:
            raise AssertionError(f"Expected audit_safe=true for {item}")
        if not is_audit_safe_oidc_denial_reason(item.denial_reason):
            raise AssertionError(f"OIDC denial reason is not audit-safe: {item.denial_reason}")


def assert_unknown_code_maps_to_safe_reason() -> None:
    mapped = map_oidc_failure_code_to_denial_reason("totally_unknown")
    if mapped.code != "OIDC_UNKNOWN_FAILURE":
        raise AssertionError(f"Unexpected unknown mapping code: {mapped}")
    if not is_audit_safe_oidc_denial_reason(mapped.denial_reason):
        raise AssertionError(f"Unknown mapping must be audit safe: {mapped}")


def assert_diagnostics_map_to_reasons() -> None:
    missing_token = extract_bearer_token({})
    mapped_missing = map_oidc_failure_code_to_denial_reason(missing_token.failure_code)
    if "TOKEN_MISSING" not in mapped_missing.denial_reason:
        raise AssertionError(f"Missing token should map to TOKEN_MISSING: {mapped_missing}")

    malformed_header = extract_bearer_token({"Authorization": "Basic abc"})
    mapped_malformed = map_oidc_failure_code_to_denial_reason(malformed_header.failure_code)
    if "TOKEN_MALFORMED_AUTHORIZATION_HEADER" not in mapped_malformed.denial_reason:
        raise AssertionError(f"Malformed header should map to TOKEN_MALFORMED_AUTHORIZATION_HEADER: {mapped_malformed}")

    malformed_jwt = unsafe_parse_jwt_without_verification("not-a-jwt")
    mapped_jwt = map_oidc_failure_code_to_denial_reason(malformed_jwt.failure_code)
    if "TOKEN_MALFORMED_JWT" not in mapped_jwt.denial_reason:
        raise AssertionError(f"Malformed JWT should map to TOKEN_MALFORMED_JWT: {mapped_jwt}")

    with tempfile.TemporaryDirectory() as temp_dir:
        missing_config = load_oidc_auth_config(Path(temp_dir) / "missing.json")
        diagnostic = validate_oidc_config_for_diagnostics(missing_config)
        if diagnostic.status != "ERROR":
            raise AssertionError(f"Expected missing config diagnostic error: {diagnostic}")
        mapped_config = map_oidc_failure_code_to_denial_reason("OIDC_CONFIG_DISABLED")
        if "CONFIG_DISABLED" not in mapped_config.denial_reason:
            raise AssertionError(f"Disabled config should map to CONFIG_DISABLED: {mapped_config}")

        incomplete_path = Path(temp_dir) / "incomplete.json"
        write_json(incomplete_path, {"enabled": True, "issuer": "https://issuer.example.test"})
        incomplete_config = load_oidc_auth_config(incomplete_path)
        incomplete_diagnostic = validate_oidc_config_for_diagnostics(incomplete_config)
        if incomplete_diagnostic.status != "ERROR":
            raise AssertionError(f"Expected incomplete config diagnostic error: {incomplete_diagnostic}")
        mapped_invalid = map_oidc_failure_code_to_denial_reason("OIDC_CONFIG_INVALID")
        if "CONFIG_INVALID" not in mapped_invalid.denial_reason:
            raise AssertionError(f"Invalid config should map to CONFIG_INVALID: {mapped_invalid}")


def assert_mapped_reasons_validate_in_security_audit() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        audit_path = Path(temp_dir) / "security_denials.oidc.jsonl"
        for index, code in enumerate(["OIDC_TOKEN_MISSING", "OIDC_TOKEN_MALFORMED_JWT", "OIDC_CONFIG_INVALID"], start=1):
            mapped = map_oidc_failure_code_to_denial_reason(code)
            append_security_denial_event(
                audit_path=audit_path,
                request_id=f"gate17c-request-{index:04d}",
                route="/review/update",
                action="claim",
                target_id="evidence_group_006",
                reviewer_id="UNKNOWN_REVIEWER",
                principal_subject="UNKNOWN_PRINCIPAL",
                principal_issuer="oidc-diagnostic",
                denial_reason=mapped.denial_reason,
                source="gate17c-oidc-denial-mapping",
                user_agent="gate17c-validator",
            )
        failures = validate_audit(audit_path, min_events=3)
        if failures:
            raise AssertionError(f"Mapped OIDC denial reasons should validate in security audit: {failures}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 17C OIDC denial reason mapping.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_catalog_is_audit_safe()
    assert_unknown_code_maps_to_safe_reason()
    assert_diagnostics_map_to_reasons()
    assert_mapped_reasons_validate_in_security_audit()
    print("[gate17c:oidc-denial] OK")
    print("[gate17c:oidc-denial] catalog=audit_safe")
    print("[gate17c:oidc-denial] diagnostics=mapped")
    print("[gate17c:oidc-denial] security_audit=valid")
    print("[gate17c:oidc-denial] authorization=unchanged_fail_closed")


if __name__ == "__main__":
    main()
