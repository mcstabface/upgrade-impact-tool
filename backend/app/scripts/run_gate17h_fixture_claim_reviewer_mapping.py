from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/fixture_claim_reviewer_mapper.py",
    "backend/app/scripts/validate_fixture_claim_reviewer_mapper.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate17h]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 17H fixture claim validation and reviewer mapping checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate17h] Starting fixture claim validation and reviewer mapping pipeline")
    print(f"[gate17h] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate17h] Expected source files are missing:")
        for path in missing:
            print(f"[gate17h]   missing: {path}")
        raise SystemExit(1)

    print("[gate17h] Validate fixture claim reviewer mapper")
    run_module("app.scripts.validate_fixture_claim_reviewer_mapper", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate17h] Dry run complete")
        return

    print("[gate17h] Pipeline complete")
    print("[gate17h] Fixture claim mapping remains local-only and non-authorizing")


if __name__ == "__main__":
    main()
