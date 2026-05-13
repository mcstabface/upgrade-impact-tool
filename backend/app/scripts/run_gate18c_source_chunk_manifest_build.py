from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/build_embedding_manifest_from_chunks.py",
    "backend/app/scripts/validate_gate18c_source_chunk_manifest_build.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18c]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 18C source chunk manifest discovery and skeleton build checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18c] Starting source chunk manifest discovery and skeleton build pipeline")
    print(f"[gate18c] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18c] Expected source files are missing:")
        for path in missing:
            print(f"[gate18c]   missing: {path}")
        raise SystemExit(1)

    print("[gate18c] Validate source chunk manifest discovery and skeleton build")
    run_module("app.scripts.validate_gate18c_source_chunk_manifest_build", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18c] Dry run complete")
        return

    print("[gate18c] Pipeline complete")
    print("[gate18c] Source chunks normalize into an embedding manifest skeleton without vectors")


if __name__ == "__main__":
    main()
