from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/oidc_denial_reasons.py",
    "backend/app/scripts/validate_oidc_denial_reason_mapping.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate17c]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 17C OIDC denial reason mapping validation.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate17c] Starting OIDC denial reason mapping validation pipeline")
    print(f"[gate17c] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate17c] Expected source files are missing:")
        for path in missing:
            print(f"[gate17c]   missing: {path}")
        raise SystemExit(1)

    print("[gate17c] Validate OIDC denial reason mapping")
    run_module("app.scripts.validate_oidc_denial_reason_mapping", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate17c] Dry run complete")
        return

    print("[gate17c] Pipeline complete")
    print("[gate17c] OIDC diagnostic failures map to audit-safe denial reasons without authorizing requests")


if __name__ == "__main__":
    main()
