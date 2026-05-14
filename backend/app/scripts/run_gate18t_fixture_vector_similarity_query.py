from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/fixture_vector_similarity_query.py",
    "backend/app/scripts/validate_fixture_vector_similarity_query.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18t]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18T fixture vector similarity query checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument(
        "--vector-jsonl",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_vectors.v1.jsonl",
    )
    parser.add_argument(
        "--readiness-report",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_vector_retrieval_readiness.v1.json",
    )
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_fixture_vector_similarity_query.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18t] Starting fixture vector similarity query pipeline")
    print(f"[gate18t] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18t] Expected source files are missing:")
        for path in missing:
            print(f"[gate18t]   missing: {path}")
        raise SystemExit(1)

    print("[gate18t] Run fixture vector similarity query")
    run_module(
        "app.scripts.fixture_vector_similarity_query",
        [
            "--vector-jsonl",
            str(args.vector_jsonl),
            "--readiness-report",
            str(args.readiness_report),
            "--top-k",
            str(args.top_k),
            "--output",
            str(args.output),
        ],
        dry_run=args.dry_run,
    )

    print("[gate18t] Validate fixture vector similarity query")
    run_module("app.scripts.validate_fixture_vector_similarity_query", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18t] Dry run complete")
        return

    print("[gate18t] Pipeline complete")
    print("[gate18t] Fixture vector similarity query is deterministic; production retrieval remains disabled")


if __name__ == "__main__":
    main()
