from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/hybrid_retrieval_design_contract.py",
    "backend/app/scripts/validate_hybrid_retrieval_design_contract.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate19a]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 19A hybrid retrieval design contract checks.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_hybrid_retrieval_design_contract.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()
    print("[gate19a] Starting hybrid retrieval design contract pipeline")
    print(f"[gate19a] Repository root: {repository_root}")
    missing = verify_source_files(repository_root)
    if missing:
        print("[gate19a] Expected source files are missing:")
        for path in missing:
            print(f"[gate19a]   missing: {path}")
        raise SystemExit(1)
    print("[gate19a] Build hybrid retrieval design contract")
    run_module(
        "app.scripts.hybrid_retrieval_design_contract",
        ["--output", str(args.output)],
        dry_run=args.dry_run,
    )
    print("[gate19a] Validate hybrid retrieval design contract")
    run_module("app.scripts.validate_hybrid_retrieval_design_contract", [], dry_run=args.dry_run)
    if args.dry_run:
        print("[gate19a] Dry run complete")
        return
    print("[gate19a] Pipeline complete")
    print("[gate19a] Hybrid retrieval remains design-only; BM25 remains authoritative")


if __name__ == "__main__":
    main()
