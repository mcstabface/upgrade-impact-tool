from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/update_redaction_review_decisions.py",
    "backend/app/scripts/validate_redaction_review_decision_updates.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18k]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 18K redaction review decision update checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18k] Starting redaction review decision update pipeline")
    print(f"[gate18k] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18k] Expected source files are missing:")
        for path in missing:
            print(f"[gate18k]   missing: {path}")
        raise SystemExit(1)

    print("[gate18k] Validate redaction review decision updates")
    run_module("app.scripts.validate_redaction_review_decision_updates", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18k] Dry run complete")
        return

    print("[gate18k] Pipeline complete")
    print("[gate18k] Redaction review decisions can be updated without enabling embedding submission")


if __name__ == "__main__":
    main()
