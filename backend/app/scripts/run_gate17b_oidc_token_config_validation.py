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
    print(f"[gate17b]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 17B OIDC token/config diagnostic validation.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate17b] Starting OIDC token/config diagnostic validation pipeline")
    print(f"[gate17b] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate17b] Expected source files are missing:")
        for path in missing:
            print(f"[gate17b]   missing: {path}")
        raise SystemExit(1)

    print("[gate17b] Validate inert OIDC diagnostics")
    run_module("app.scripts.validate_oidc_auth_adapter_skeleton", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate17b] Dry run complete")
        return

    print("[gate17b] Pipeline complete")
    print("[gate17b] Bearer token parsing and JWT parsing remain diagnostic-only and non-authorizing")


if __name__ == "__main__":
    main()
