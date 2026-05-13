from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/disabled_oidc_smoke_harness.py",
    "backend/app/scripts/validate_disabled_oidc_smoke_harness.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate17d]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 17D disabled OIDC smoke harness validation.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate17d] Starting disabled OIDC smoke harness validation pipeline")
    print(f"[gate17d] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate17d] Expected source files are missing:")
        for path in missing:
            print(f"[gate17d]   missing: {path}")
        raise SystemExit(1)

    print("[gate17d] Validate disabled OIDC smoke harness")
    run_module("app.scripts.validate_disabled_oidc_smoke_harness", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate17d] Dry run complete")
        return

    print("[gate17d] Pipeline complete")
    print("[gate17d] Disabled OIDC smoke failures write valid security-denial audit events without authorizing requests")


if __name__ == "__main__":
    main()
