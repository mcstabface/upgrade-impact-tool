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
    content = read_text(path)
    failures: list[ValidationFailure] = []
    required_fragments = [
        "Gate 16A Production Auth Design Spec",
        "Gate 15 is explicitly local-development authorization",
        "Identity Provider Requirements",
        "Reviewer Identity Mapping",
        "Role Model",
        "Permission Checks",
        "Trusted Request Validation",
        "Request Provenance Requirements",
        "Audit Hardening",
        "Configuration and Secrets",
        "Failure Behavior",
        "Browser Mutation Requirements",
        "Production Readiness Gates",
        "Migration Path from Gate 15",
        "Gate 16B — Auth Adapter Interface and Security Audit Events",
    ]
    for fragment in required_fragments:
        if fragment not in content:
            failures.append(ValidationFailure("required_fragment", f"Missing required fragment: {fragment!r}."))

    provider_fragments = ["OIDC interactive login", "Reverse-proxy asserted identity", "Signed service token"]
    for fragment in provider_fragments:
        if fragment not in content:
            failures.append(ValidationFailure("identity_provider_option", f"Missing identity provider option: {fragment!r}."))

    required_roles = ["review_observer", "reviewer", "lead_reviewer", "admin"]
    for role in required_roles:
        if role not in content:
            failures.append(ValidationFailure("role_model", f"Missing production role: {role!r}."))

    required_failure_codes = ["401 Unauthorized", "403 Forbidden", "400 Bad Request", "409 Conflict", "500"]
    for code in required_failure_codes:
        if code not in content:
            failures.append(ValidationFailure("failure_behavior", f"Missing failure behavior code: {code!r}."))

    forbidden_fragments = [
        "production secrets in Git",
        "finalization_allowed = true",
    ]
    lowered = content.lower()
    for fragment in forbidden_fragments:
        if fragment.lower() in lowered:
            failures.append(ValidationFailure("forbidden_fragment", f"Forbidden fragment found: {fragment!r}."))

    if content.count("finalization remains disabled") < 2:
        failures.append(ValidationFailure("finalization_control", "Expected repeated finalization-disabled language."))
    if "Do not rely on client-supplied reviewer ID as the sole identity source in production." not in content:
        failures.append(ValidationFailure("identity_mapping", "Expected warning against client-supplied reviewer ID as sole identity source."))
    if "Browser mutation must not write JSON files directly." not in content:
        failures.append(ValidationFailure("browser_safety", "Expected direct JSON mutation prohibition."))

    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 16A production auth design spec coverage.")
    parser.add_argument("--spec", type=Path, default=root / "docs" / "security" / "Gate 16A Production Auth Design Spec.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate_design_spec(args.spec)
    if failures:
        print("[gate16a:validate] FAILED")
        for failure in failures:
            print(f"[gate16a:validate] {failure.check}: {failure.detail}")
        raise SystemExit(1)
    print("[gate16a:validate] OK")
    print(f"[gate16a:validate] spec={args.spec}")


if __name__ == "__main__":
    main()
