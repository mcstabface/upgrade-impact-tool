from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from app.scripts.disabled_adapter_selection_smoke import (
    run_disabled_oidc_adapter_selection_smoke,
    select_adapter_for_disabled_smoke,
)
from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.validate_security_denial_audit import read_events, validate_audit


def assert_unsupported_adapter_fails() -> None:
    try:
        select_adapter_for_disabled_smoke("not-real")
    except ValueError as exc:
        if "Unsupported adapter" not in str(exc):
            raise AssertionError(f"Unexpected unsupported-adapter error: {exc}") from exc
        return
    raise AssertionError("Unsupported adapter selection must fail.")


def assert_local_policy_requires_policy_path() -> None:
    try:
        select_adapter_for_disabled_smoke("local_policy")
    except ValueError as exc:
        if "policy_path is required" not in str(exc):
            raise AssertionError(f"Unexpected local-policy error: {exc}") from exc
        return
    raise AssertionError("Local policy selection without policy path must fail.")


def assert_disabled_oidc_selection_writes_valid_audit() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        audit_path = Path(temp_dir) / "security_denials.gate17i.jsonl"
        result = run_disabled_oidc_adapter_selection_smoke(audit_path=audit_path)
        if result.adapter_name != "oidc_disabled" or result.selected is not True:
            raise AssertionError(f"Unexpected adapter selection result: {result}")
        if result.authorization_allowed is not False:
            raise AssertionError(f"Disabled adapter smoke must not authorize: {result}")
        if not result.audit_event_id:
            raise AssertionError(f"Expected audit event id: {result}")

        failures = validate_audit(audit_path, min_events=1)
        if failures:
            raise AssertionError(f"Disabled adapter smoke audit must validate: {failures}")
        events = read_events(audit_path)
        if len(events) != 1:
            raise AssertionError(f"Expected one audit event, got: {events}")
        event = events[0]
        if event.get("principal_issuer") != "oidc-disabled-adapter-selection":
            raise AssertionError(f"Unexpected principal issuer: {event}")
        if event.get("source") != "gate17i-disabled-adapter-selection-smoke":
            raise AssertionError(f"Unexpected source: {event}")
        if not str(event.get("denial_reason", "")).startswith("OIDC_DENIAL:"):
            raise AssertionError(f"Expected OIDC denial reason: {event}")
        if event.get("finalization_allowed") is not False:
            raise AssertionError(f"Finalization must remain disabled: {event}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 17I disabled adapter selection smoke.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_unsupported_adapter_fails()
    assert_local_policy_requires_policy_path()
    assert_disabled_oidc_selection_writes_valid_audit()
    print("[gate17i:adapter-selection] OK")
    print("[gate17i:adapter-selection] unsupported_adapter=fail_closed")
    print("[gate17i:adapter-selection] local_policy_requires_policy_path=true")
    print("[gate17i:adapter-selection] oidc_disabled=selected_and_denied")
    print("[gate17i:adapter-selection] security_audit=valid")
    print("[gate17i:adapter-selection] authorization=unchanged_disabled")


if __name__ == "__main__":
    main()
