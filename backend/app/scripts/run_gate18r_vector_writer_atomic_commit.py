from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/vector_writer_atomic_commit.py",
    "backend/app/scripts/validate_vector_writer_atomic_commit.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18r]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18R vector writer atomic commit checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument(
        "--response-fixture",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_response_fixture.v1.jsonl",
    )
    parser.add_argument(
        "--commit-gate",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_vector_writer_commit_gate.v1.json",
    )
    parser.add_argument(
        "--vector-output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_vectors.v1.jsonl",
    )
    parser.add_argument(
        "--index-output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_vector_index.v1.json",
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_vector_writer_atomic_commit_report.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18r] Starting vector writer atomic commit pipeline")
    print(f"[gate18r] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18r] Expected source files are missing:")
        for path in missing:
            print(f"[gate18r]   missing: {path}")
        raise SystemExit(1)

    print("[gate18r] Commit fixture vectors atomically")
    run_module(
        "app.scripts.vector_writer_atomic_commit",
        [
            "--response-fixture",
            str(args.response_fixture),
            "--commit-gate",
            str(args.commit_gate),
            "--vector-output",
            str(args.vector_output),
            "--index-output",
            str(args.index_output),
            "--report-output",
            str(args.report_output),
        ],
        dry_run=args.dry_run,
    )

    print("[gate18r] Validate vector writer atomic commit behavior")
    run_module("app.scripts.validate_vector_writer_atomic_commit", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18r] Dry run complete")
        return

    print("[gate18r] Pipeline complete")
    print("[gate18r] Fixture vector outputs were committed atomically")


if __name__ == "__main__":
    main()
