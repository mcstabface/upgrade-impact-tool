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
        "Gate 17J OIDC Endpoint Integration Design Spec",
        "This gate is design-only",
        "does not change the live endpoint",
        "does not enable OIDC",
        "Default must remain:",
        "local_policy",
        "allow_oidc_adapter = true",
        "If any condition fails, the endpoint must deny before mutation",
        "write a security-denial audit event",
        "denial_reason = OIDC_DENIAL:<CATEGORY>:<MESSAGE>",
        "Request provenance must remain mandatory",
        "missing request ID before mutation",
        "Rollback must not require code deletion",
        "Gate 17K — Endpoint Adapter Selection Config Skeleton",
    ]
    for fragment in required_fragments:
        if fragment not in text:
            failures.append(ValidationFailure("required_fragment", f"Missing required fragment: {fragment!r}"))

    required_sections = [
        "## Purpose",
        "## Baseline",
        "## Required Integration Rule",
        "## OIDC Enablement Guardrails",
        "## Fail-Closed Requirements",
        "## Audit Requirements",
        "## Provenance Requirements",
        "## Mutation Requirements",
        "## Rollback Requirements",
        "## Required Test Matrix Before Implementation",
        "## Recommended Next Gate",
    ]
    for section in required_sections:
        if section not in text:
            failures.append(ValidationFailure("required_section", f"Missing required section: {section!r}"))

    forbidden_fragments = [
        "OIDC is enabled by default",
        "default must be oidc",
        "provenance may be skipped",
        "finalization_allowed = true",
    ]
    text_lower = text.lower()
    for fragment in forbidden_fragments:
        if fragment.lower() in text_lower:
            failures.append(ValidationFailure("forbidden_fragment", f"Forbidden design claim found: {fragment!r}"))
    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 17J OIDC endpoint integration design spec.")
    parser.add_argument(
        "--spec",
        type=Path,
        default=root / "docs" / "checkpoints" / "Gate 17J OIDC Endpoint Integration Design Spec.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate_design_spec(args.spec)
    if failures:
        print("[gate17j:design] FAILED")
        for failure in failures:
            print(f"[gate17j:design] {failure.check}: {failure.detail}")
        raise SystemExit(1)
    print("[gate17j:design] OK")
    print("[gate17j:design] endpoint_integration=specified_not_implemented")
    print("[gate17j:design] local_policy_default=preserved")
    print("[gate17j:design] oidc_enablement=explicit_only")
    print("[gate17j:design] provenance_required=preserved")


if __name__ == "__main__":
    main()
