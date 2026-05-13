from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/embedding_manifest_skeleton.py",
    "backend/app/scripts/validate_embedding_manifest_skeleton.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18b]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 18B embedding manifest skeleton checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18b] Starting embedding manifest skeleton pipeline")
    print(f"[gate18b] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18b] Expected source files are missing:")
        for path in missing:
            print(f"[gate18b]   missing: {path}")
        raise SystemExit(1)

    print("[gate18b] Validate embedding manifest skeleton")
    run_module("app.scripts.validate_embedding_manifest_skeleton", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18b] Dry run complete")
        return

    print("[gate18b] Pipeline complete")
    print("[gate18b] Embedding manifest skeleton remains non-embedding and cache-key only")


if __name__ == "__main__":
    main()
