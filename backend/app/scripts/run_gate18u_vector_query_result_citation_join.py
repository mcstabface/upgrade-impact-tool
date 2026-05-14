from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/vector_query_result_citation_join.py",
    "backend/app/scripts/validate_vector_query_result_citation_join.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18u]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18U vector query result citation join checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument(
        "--query-report",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_fixture_vector_similarity_query.v1.json",
    )
    parser.add_argument(
        "--request-jsonl",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_full_text_requests.v1.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_fixture_vector_citation_join.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18u] Starting vector query result citation join pipeline")
    print(f"[gate18u] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18u] Expected source files are missing:")
        for path in missing:
            print(f"[gate18u]   missing: {path}")
        raise SystemExit(1)

    print("[gate18u] Join vector query results to citation payloads")
    run_module(
        "app.scripts.vector_query_result_citation_join",
        [
            "--query-report",
            str(args.query_report),
            "--request-jsonl",
            str(args.request_jsonl),
            "--output",
            str(args.output),
        ],
        dry_run=args.dry_run,
    )

    print("[gate18u] Validate vector query result citation join")
    run_module("app.scripts.validate_vector_query_result_citation_join", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18u] Dry run complete")
        return

    print("[gate18u] Pipeline complete")
    print("[gate18u] Fixture vector query results are joined to citation payloads; production retrieval remains disabled")


if __name__ == "__main__":
    main()
