from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/hybrid_retrieval_citation_preservation_validator.py",
    "backend/app/scripts/validate_hybrid_retrieval_citation_preservation.py",
    "backend/app/scripts/hybrid_retrieval_score_normalization_design.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate19d]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 19D hybrid retrieval citation preservation checks.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--score-design",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_hybrid_retrieval_score_normalization_design.v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_hybrid_retrieval_citation_preservation.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()
    print("[gate19d] Starting hybrid retrieval citation preservation pipeline")
    print(f"[gate19d] Repository root: {repository_root}")
    missing = verify_source_files(repository_root)
    if missing:
        print("[gate19d] Expected source files are missing:")
        for path in missing:
            print(f"[gate19d]   missing: {path}")
        raise SystemExit(1)
    print("[gate19d] Build hybrid retrieval citation preservation report")
    run_module(
        "app.scripts.hybrid_retrieval_citation_preservation_validator",
        ["--score-design", str(args.score_design), "--output", str(args.output)],
        dry_run=args.dry_run,
    )
    print("[gate19d] Validate hybrid retrieval citation preservation")
    run_module("app.scripts.validate_hybrid_retrieval_citation_preservation", [], dry_run=args.dry_run)
    if args.dry_run:
        print("[gate19d] Dry run complete")
        return
    print("[gate19d] Pipeline complete")
    print("[gate19d] Hybrid retrieval citation preservation is valid; merged results remain disabled")


if __name__ == "__main__":
    main()
