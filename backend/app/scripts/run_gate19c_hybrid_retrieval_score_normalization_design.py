from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/hybrid_retrieval_score_normalization_design.py",
    "backend/app/scripts/validate_hybrid_retrieval_score_normalization_design.py",
    "backend/app/scripts/hybrid_retrieval_fixture_merge_plan.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate19c]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 19C hybrid retrieval score normalization design checks.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--fixture-merge-plan",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_hybrid_retrieval_fixture_merge_plan.v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_hybrid_retrieval_score_normalization_design.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()
    print("[gate19c] Starting hybrid retrieval score normalization design pipeline")
    print(f"[gate19c] Repository root: {repository_root}")
    missing = verify_source_files(repository_root)
    if missing:
        print("[gate19c] Expected source files are missing:")
        for path in missing:
            print(f"[gate19c]   missing: {path}")
        raise SystemExit(1)
    print("[gate19c] Build hybrid retrieval score normalization design")
    run_module(
        "app.scripts.hybrid_retrieval_score_normalization_design",
        ["--fixture-merge-plan", str(args.fixture_merge_plan), "--output", str(args.output)],
        dry_run=args.dry_run,
    )
    print("[gate19c] Validate hybrid retrieval score normalization design")
    run_module("app.scripts.validate_hybrid_retrieval_score_normalization_design", [], dry_run=args.dry_run)
    if args.dry_run:
        print("[gate19c] Dry run complete")
        return
    print("[gate19c] Pipeline complete")
    print("[gate19c] Score normalization remains design-only; no merged results are emitted")


if __name__ == "__main__":
    main()
