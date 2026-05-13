from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/fixture_jwt_signature_validator.py",
    "backend/app/scripts/validate_fixture_jwt_signature_validator.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate17g]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 17G fixture JWT signature validation checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate17g] Starting fixture JWT signature validation pipeline")
    print(f"[gate17g] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate17g] Expected source files are missing:")
        for path in missing:
            print(f"[gate17g]   missing: {path}")
        raise SystemExit(1)

    print("[gate17g] Validate fixture JWT signature helper")
    run_module("app.scripts.validate_fixture_jwt_signature_validator", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate17g] Dry run complete")
        return

    print("[gate17g] Pipeline complete")
    print("[gate17g] Fixture JWT signature validation remains local-only and non-authorizing")


if __name__ == "__main__":
    main()
