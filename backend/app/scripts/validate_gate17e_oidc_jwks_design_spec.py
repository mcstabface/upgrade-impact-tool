from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


@dataclass(frozen=True)
class ValidationFailure:
    check: str
    detail: str


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Required design spec not found: {path}")
    return path.read_text(encoding="utf-8")


def validate_design_spec(path: Path) -> list[ValidationFailure]:
    text = read_text(path)
    failures: list[ValidationFailure] = []

    required_fragments = [
        "Gate 17E OIDC JWKS Validation Design Spec",
        "Gate 17E is a design gate only",
        "does not implement JWT signature validation",
        "does not fetch JWKS",
        "does not accept tokens",
        "does not replace `LocalPolicyAuthAdapter`",
        "finalization remains disabled",
        "issuer/audience requirements",
        "JWKS retrieval and caching policy",
        "accepted algorithms",
        "clock-skew policy",
        "claim-to-reviewer mapping",
        "security-denial audit integration",
        "explicit enablement guardrails",
        "RS256",
        "OIDC_DENIAL:<CATEGORY>:<AUDIT_SAFE_MESSAGE>",
        "TOKEN_SIGNATURE_INVALID",
        "TOKEN_KEY_NOT_FOUND",
        "TOKEN_ALGORITHM_REJECTED",
        "TOKEN_ISSUER_INVALID",
        "TOKEN_AUDIENCE_INVALID",
        "TOKEN_EXPIRED",
        "TOKEN_NOT_YET_VALID",
        "REQUIRED_GROUP_MISSING",
        "Gate 17F — Local JWKS Fixture Validation Helper",
    ]
    for fragment in required_fragments:
        if fragment not in text:
            failures.append(ValidationFailure("required_fragment", f"Missing required fragment: {fragment!r}."))

    required_sections = [
        "## Purpose",
        "## Source Baseline",
        "## Design Goals",
        "## Non-Goals",
        "## Proposed Config Contract",
        "## Issuer and Audience Requirements",
        "## JWKS Retrieval and Cache Policy",
        "## Accepted Algorithms",
        "## Time Claim Policy",
        "## Claim-to-Reviewer Mapping",
        "## Security-Denial Audit Integration",
        "## Endpoint Integration Guardrails",
        "## Minimum Test Matrix for Implementation Gate",
        "## Recommended Implementation Sequence",
        "## Completion Criteria for Gate 17E",
    ]
    for section in required_sections:
        if section not in text:
            failures.append(ValidationFailure("required_section", f"Missing required section: {section!r}."))

    forbidden_fragments = [
        "accepts tokens in Gate 17E",
        "wire OIDC into the guarded endpoint in Gate 17E",
        "replace `LocalPolicyAuthAdapter` in Gate 17E",
        "enable finalization",
    ]
    for fragment in forbidden_fragments:
        if fragment in text:
            failures.append(ValidationFailure("forbidden_fragment", f"Forbidden design claim found: {fragment!r}."))

    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 17E OIDC JWKS validation design spec.")
    parser.add_argument(
        "--spec",
        type=Path,
        default=root / "docs" / "checkpoints" / "Gate 17E OIDC JWKS Validation Design Spec.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate_design_spec(args.spec)
    if failures:
        print("[gate17e:design] FAILED")
        for failure in failures:
            print(f"[gate17e:design] {failure.check}: {failure.detail}")
        raise SystemExit(1)
    print("[gate17e:design] OK")
    print("[gate17e:design] jwks_validation=specified_not_implemented")
    print("[gate17e:design] token_acceptance=forbidden")
    print("[gate17e:design] endpoint_wiring=forbidden")
    print("[gate17e:design] local_policy_default=preserved")


if __name__ == "__main__":
    main()
