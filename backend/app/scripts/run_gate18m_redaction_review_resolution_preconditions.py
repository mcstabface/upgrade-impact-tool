from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/redaction_review_resolution_preconditions.py",
    "backend/app/scripts/validate_redaction_review_resolution_preconditions.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18m]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18M review resolution fixture and submission precondition checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument(
        "--review-export",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_unresolved_redaction_review.v1.json",
    )
    parser.add_argument(
        "--fixture-output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_redaction_review_resolution_fixture.v1.json",
    )
    parser.add_argument(
        "--precondition-output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_submission_preconditions.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18m] Starting redaction review resolution precondition pipeline")
    print(f"[gate18m] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18m] Expected source files are missing:")
        for path in missing:
            print(f"[gate18m]   missing: {path}")
        raise SystemExit(1)

    print("[gate18m] Build resolution fixture and submission precondition report")
    run_module(
        "app.scripts.redaction_review_resolution_preconditions",
        [
            "--review-export",
            str(args.review_export),
            "--fixture-output",
            str(args.fixture_output),
            "--precondition-output",
            str(args.precondition_output),
        ],
        dry_run=args.dry_run,
    )

    print("[gate18m] Validate resolution fixture and submission preconditions")
    run_module("app.scripts.validate_redaction_review_resolution_preconditions", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18m] Dry run complete")
        return

    print("[gate18m] Pipeline complete")
    print("[gate18m] Submission preconditions are ready in dry-run only; real embedding submission remains disabled")


if __name__ == "__main__":
    main()
