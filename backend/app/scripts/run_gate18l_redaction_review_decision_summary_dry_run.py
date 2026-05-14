from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/redaction_review_decision_summary_dry_run.py",
    "backend/app/scripts/validate_redaction_review_decision_summary_dry_run.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18l]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18L redaction review decision summary dry-run checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument(
        "--review-export",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_unresolved_redaction_review.v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_redaction_review_decision_summary.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18l] Starting redaction review decision summary dry-run pipeline")
    print(f"[gate18l] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18l] Expected source files are missing:")
        for path in missing:
            print(f"[gate18l]   missing: {path}")
        raise SystemExit(1)

    print("[gate18l] Build redaction review decision summary report")
    run_module(
        "app.scripts.redaction_review_decision_summary_dry_run",
        ["--review-export", str(args.review_export), "--output", str(args.output)],
        dry_run=args.dry_run,
    )

    print("[gate18l] Validate redaction review decision summary dry run")
    run_module("app.scripts.validate_redaction_review_decision_summary_dry_run", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18l] Dry run complete")
        return

    print("[gate18l] Pipeline complete")
    print("[gate18l] Redaction review decisions are summarized without enabling embedding submission")


if __name__ == "__main__":
    main()
