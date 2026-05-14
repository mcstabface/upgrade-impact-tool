from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/embedding_response_fixture_vector_writer_design.py",
    "backend/app/scripts/validate_embedding_response_fixture_vector_writer_design.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18o]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18O embedding response fixture and vector writer design checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument(
        "--request-jsonl",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_full_text_requests.v1.jsonl",
    )
    parser.add_argument(
        "--response-fixture-output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_response_fixture.v1.jsonl",
    )
    parser.add_argument(
        "--design-output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_vector_writer_design.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18o] Starting embedding response fixture vector writer design pipeline")
    print(f"[gate18o] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18o] Expected source files are missing:")
        for path in missing:
            print(f"[gate18o]   missing: {path}")
        raise SystemExit(1)

    print("[gate18o] Build embedding response fixture and vector writer design")
    run_module(
        "app.scripts.embedding_response_fixture_vector_writer_design",
        [
            "--request-jsonl",
            str(args.request_jsonl),
            "--response-fixture-output",
            str(args.response_fixture_output),
            "--design-output",
            str(args.design_output),
        ],
        dry_run=args.dry_run,
    )

    print("[gate18o] Validate embedding response fixture and vector writer design")
    run_module("app.scripts.validate_embedding_response_fixture_vector_writer_design", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18o] Dry run complete")
        return

    print("[gate18o] Pipeline complete")
    print("[gate18o] Response fixture and vector writer contract are design-only; vectors are not created")


if __name__ == "__main__":
    main()
