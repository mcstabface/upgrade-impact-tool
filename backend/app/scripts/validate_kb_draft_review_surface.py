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
        raise FileNotFoundError(f"Required file not found: {path}")
    return path.read_text(encoding="utf-8")


def validate_surface(path: Path) -> list[ValidationFailure]:
    html = read_text(path)
    failures: list[ValidationFailure] = []
    required_fragments = [
        "KB Draft Review Surface",
        "Read-only Gate 11 surface",
        "Review mutation must use Gate 10 update commands",
        "Claim Review Tasks",
        "Unresolved Gap Acknowledgement Tasks",
        "Review Policy",
        "Finalization allowed",
        "Visual review tasks",
        "Evidence lineage",
    ]
    for fragment in required_fragments:
        if fragment not in html:
            failures.append(ValidationFailure("required_fragment", f"Missing required fragment: {fragment!r}."))

    forbidden_fragments = [
        "<form",
        "method=",
        "onclick=",
        "fetch(",
        "XMLHttpRequest",
        "contenteditable",
    ]
    for fragment in forbidden_fragments:
        if fragment in html:
            failures.append(ValidationFailure("read_only_surface", f"Forbidden mutation-capable fragment found: {fragment!r}."))

    if html.count("claim-card") < 15:
        failures.append(ValidationFailure("claim_cards", "Expected at least 15 claim-card entries."))
    if html.count("gap-card") < 10:
        failures.append(ValidationFailure("gap_cards", "Expected at least 10 gap-card entries."))
    if "readonly" not in html:
        failures.append(ValidationFailure("readonly_fields", "Expected readonly reviewer fields."))

    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 11 read-only KB draft review UI surface.")
    parser.add_argument("--surface", type=Path, default=root / "kbs" / "manifests" / "kb_draft_review_surface.html")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate_surface(args.surface)
    if failures:
        print("[gate11:validate] FAILED")
        for failure in failures:
            print(f"[gate11:validate] {failure.check}: {failure.detail}")
        raise SystemExit(1)
    print("[gate11:validate] OK")
    print(f"[gate11:validate] surface={args.surface}")


if __name__ == "__main__":
    main()
