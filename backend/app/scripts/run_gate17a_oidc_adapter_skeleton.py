from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/oidc_auth_adapter.py",
    "backend/app/scripts/validate_oidc_auth_adapter_skeleton.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate17a]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 17A inert OIDC adapter skeleton validation.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate17a] Starting OIDC adapter skeleton validation pipeline")
    print(f"[gate17a] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate17a] Expected source files are missing:")
        for path in missing:
            print(f"[gate17a]   missing: {path}")
        raise SystemExit(1)

    print("[gate17a] Validate inert OIDC adapter skeleton")
    run_module("app.scripts.validate_oidc_auth_adapter_skeleton", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate17a] Dry run complete")
        return

    print("[gate17a] Pipeline complete")
    print("[gate17a] OIDC adapter skeleton remains disabled and fail-closed")


if __name__ == "__main__":
    main()
