from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/vector_artifact_retrieval_readiness.py",
    "backend/app/scripts/validate_vector_artifact_retrieval_readiness.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18s]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18S vector artifact retrieval readiness checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument(
        "--vector-jsonl",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_vectors.v1.jsonl",
    )
    parser.add_argument(
        "--vector-index",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_vector_index.v1.json",
    )
    parser.add_argument(
        "--atomic-commit-report",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_vector_writer_atomic_commit_report.v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_vector_retrieval_readiness.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18s] Starting vector artifact retrieval readiness pipeline")
    print(f"[gate18s] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18s] Expected source files are missing:")
        for path in missing:
            print(f"[gate18s]   missing: {path}")
        raise SystemExit(1)

    print("[gate18s] Build vector retrieval readiness report")
    run_module(
        "app.scripts.vector_artifact_retrieval_readiness",
        [
            "--vector-jsonl",
            str(args.vector_jsonl),
            "--vector-index",
            str(args.vector_index),
            "--atomic-commit-report",
            str(args.atomic_commit_report),
            "--output",
            str(args.output),
        ],
        dry_run=args.dry_run,
    )

    print("[gate18s] Validate vector artifact retrieval readiness")
    run_module("app.scripts.validate_vector_artifact_retrieval_readiness", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18s] Dry run complete")
        return

    print("[gate18s] Pipeline complete")
    print("[gate18s] Vector artifacts are validated and retrieval-ready")


if __name__ == "__main__":
    main()
