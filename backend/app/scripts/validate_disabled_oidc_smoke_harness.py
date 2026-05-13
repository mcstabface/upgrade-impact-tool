from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from app.scripts.disabled_oidc_smoke_harness import run_disabled_oidc_smoke_harness
from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.validate_security_denial_audit import read_events, validate_audit


EXPECTED_FAILURE_CODES = [
    "OIDC_TOKEN_MISSING",
    "OIDC_TOKEN_MALFORMED_AUTHORIZATION_HEADER",
    "OIDC_TOKEN_MALFORMED_JWT",
]


def assert_disabled_smoke_results_are_non_authorizing() -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        audit_path = Path(temp_dir) / "security_denials.gate17d.jsonl"
        results = run_disabled_oidc_smoke_harness(audit_path=audit_path)
        if [result.failure_code for result in results] != EXPECTED_FAILURE_CODES:
            raise AssertionError(f"Unexpected disabled OIDC smoke failure codes: {results}")
        for result in results:
            if result.authorization_allowed is not False:
                raise AssertionError(f"Disabled OIDC smoke result must not authorize: {result}")
            if not result.denial_reason.startswith("OIDC_DENIAL:"):
                raise AssertionError(f"Disabled OIDC smoke reason must use OIDC_DENIAL prefix: {result}")

        failures = validate_audit(audit_path, min_events=len(EXPECTED_FAILURE_CODES))
        if failures:
            raise AssertionError(f"Disabled OIDC smoke audit must validate: {failures}")

        events = read_events(audit_path)
        if len(events) != len(EXPECTED_FAILURE_CODES):
            raise AssertionError(f"Expected {len(EXPECTED_FAILURE_CODES)} audit events, got {len(events)}")
        for index, event in enumerate(events):
            if event.get("principal_issuer") != "oidc-disabled-smoke":
                raise AssertionError(f"Unexpected principal issuer for event {index}: {event}")
            if event.get("source") != "gate17d-disabled-oidc-smoke":
                raise AssertionError(f"Unexpected source for event {index}: {event}")
            if event.get("finalization_allowed") is not False:
                raise AssertionError(f"Finalization must remain disabled for event {index}: {event}")
            if not str(event.get("denial_reason", "")).startswith("OIDC_DENIAL:"):
                raise AssertionError(f"Expected mapped OIDC denial reason for event {index}: {event}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 17D disabled OIDC smoke harness.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_disabled_smoke_results_are_non_authorizing()
    print("[gate17d:oidc-smoke] OK")
    print("[gate17d:oidc-smoke] scenarios=3")
    print("[gate17d:oidc-smoke] denial_reasons=mapped")
    print("[gate17d:oidc-smoke] security_audit=valid")
    print("[gate17d:oidc-smoke] authorization=unchanged_disabled")


if __name__ == "__main__":
    main()
