from __future__ import annotations

import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.fixture_claim_reviewer_mapper import validate_fixture_claims_and_map_reviewer


NOW = datetime(2026, 5, 13, 16, 45, 0, tzinfo=timezone.utc)
BASE_CLAIMS: dict[str, Any] = {
    "iss": "https://issuer.example.test",
    "aud": "upgrade-impact-tool",
    "preferred_username": "GATE17H_FIXTURE",
    "name": "Gate 17H Fixture Reviewer",
    "email": "gate17h.fixture@example.test",
    "groups": ["upgrade-impact-reviewers"],
    "roles": ["reviewer"],
    "exp": int(NOW.timestamp()) + 3600,
    "nbf": int(NOW.timestamp()) - 60,
}


def failure_codes(result: object) -> list[str]:
    return [failure.code for failure in getattr(result, "failures")]


def assert_valid_claims_map_reviewer() -> None:
    result = validate_fixture_claims_and_map_reviewer(
        dict(BASE_CLAIMS),
        expected_issuer="https://issuer.example.test",
        expected_audience="upgrade-impact-tool",
        required_groups=["upgrade-impact-reviewers"],
        now_utc=NOW,
    )
    if result.status != "OK":
        raise AssertionError(f"Expected fixture claims to map, got: {result}")
    if result.authorization_allowed is not False:
        raise AssertionError("Fixture claim mapping must not authorize.")
    if not result.reviewer or result.reviewer.reviewer_id != "GATE17H_FIXTURE":
        raise AssertionError(f"Expected reviewer mapping, got: {result.reviewer}")
    if not result.principal or result.principal.auth_method != "oidc-fixture":
        raise AssertionError(f"Expected fixture principal, got: {result.principal}")


def assert_issuer_mismatch_fails() -> None:
    claims = dict(BASE_CLAIMS)
    claims["iss"] = "https://wrong.example.test"
    result = validate_fixture_claims_and_map_reviewer(
        claims,
        expected_issuer="https://issuer.example.test",
        expected_audience="upgrade-impact-tool",
        required_groups=["upgrade-impact-reviewers"],
        now_utc=NOW,
    )
    if "JWT_ISSUER_INVALID" not in failure_codes(result):
        raise AssertionError(f"Expected issuer failure, got: {result}")


def assert_audience_mismatch_fails() -> None:
    claims = dict(BASE_CLAIMS)
    claims["aud"] = "wrong-audience"
    result = validate_fixture_claims_and_map_reviewer(
        claims,
        expected_issuer="https://issuer.example.test",
        expected_audience="upgrade-impact-tool",
        required_groups=["upgrade-impact-reviewers"],
        now_utc=NOW,
    )
    if "JWT_AUDIENCE_INVALID" not in failure_codes(result):
        raise AssertionError(f"Expected audience failure, got: {result}")


def assert_expired_claim_fails() -> None:
    claims = dict(BASE_CLAIMS)
    claims["exp"] = int(NOW.timestamp()) - 3600
    result = validate_fixture_claims_and_map_reviewer(
        claims,
        expected_issuer="https://issuer.example.test",
        expected_audience="upgrade-impact-tool",
        required_groups=["upgrade-impact-reviewers"],
        now_utc=NOW,
    )
    if "JWT_EXPIRED" not in failure_codes(result):
        raise AssertionError(f"Expected expiry failure, got: {result}")


def assert_required_group_missing_fails() -> None:
    claims = dict(BASE_CLAIMS)
    claims["groups"] = []
    result = validate_fixture_claims_and_map_reviewer(
        claims,
        expected_issuer="https://issuer.example.test",
        expected_audience="upgrade-impact-tool",
        required_groups=["upgrade-impact-reviewers"],
        now_utc=NOW,
    )
    if "REQUIRED_GROUP_MISSING" not in failure_codes(result):
        raise AssertionError(f"Expected group failure, got: {result}")


def assert_missing_reviewer_claim_fails() -> None:
    claims = dict(BASE_CLAIMS)
    claims.pop("preferred_username")
    result = validate_fixture_claims_and_map_reviewer(
        claims,
        expected_issuer="https://issuer.example.test",
        expected_audience="upgrade-impact-tool",
        required_groups=["upgrade-impact-reviewers"],
        now_utc=NOW,
    )
    if "REVIEWER_MAPPING_FAILED" not in failure_codes(result):
        raise AssertionError(f"Expected reviewer mapping failure, got: {result}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 17H fixture claim reviewer mapper.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_valid_claims_map_reviewer()
    assert_issuer_mismatch_fails()
    assert_audience_mismatch_fails()
    assert_expired_claim_fails()
    assert_required_group_missing_fails()
    assert_missing_reviewer_claim_fails()
    print("[gate17h:claims] OK")
    print("[gate17h:claims] reviewer_mapping=valid")
    print("[gate17h:claims] issuer_audience=validated")
    print("[gate17h:claims] time_claims=validated")
    print("[gate17h:claims] required_groups=validated")
    print("[gate17h:claims] authorization=unchanged_disabled")


if __name__ == "__main__":
    main()
