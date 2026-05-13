from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "docs/checkpoints/Gate 18A Embedding Manifest Vector Store Design Spec.md",
    "backend/app/scripts/validate_gate18a_embedding_vector_design.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18a]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 18A embedding manifest and vector store design checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18a] Starting embedding manifest and vector store design pipeline")
    print(f"[gate18a] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18a] Expected source files are missing:")
        for path in missing:
            print(f"[gate18a]   missing: {path}")
        raise SystemExit(1)

    print("[gate18a] Validate embedding manifest and vector store design")
    run_module("app.scripts.validate_gate18a_embedding_vector_design", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18a] Dry run complete")
        return

    print("[gate18a] Pipeline complete")
    print("[gate18a] Embedding manifest and vector store remain specified but not implemented")


if __name__ == "__main__":
    main()
