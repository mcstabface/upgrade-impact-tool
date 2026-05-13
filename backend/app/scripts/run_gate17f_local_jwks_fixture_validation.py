from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/local_jwks_fixture_validator.py",
    "backend/app/scripts/validate_local_jwks_fixture_validator.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate17f]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 17F local JWKS fixture validation checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate17f] Starting local JWKS fixture validation pipeline")
    print(f"[gate17f] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate17f] Expected source files are missing:")
        for path in missing:
            print(f"[gate17f]   missing: {path}")
        raise SystemExit(1)

    print("[gate17f] Validate local JWKS fixture helper")
    run_module("app.scripts.validate_local_jwks_fixture_validator", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate17f] Dry run complete")
        return

    print("[gate17f] Pipeline complete")
    print("[gate17f] Local JWKS fixture validation remains structural and non-authorizing")


if __name__ == "__main__":
    main()
