from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/vector_writer_dry_run_validator.py",
    "backend/app/scripts/validate_vector_writer_dry_run.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18p]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18P vector writer dry-run validation.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument(
        "--response-fixture",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_response_fixture.v1.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_vector_writer_dry_run_report.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18p] Starting vector writer dry-run validation pipeline")
    print(f"[gate18p] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18p] Expected source files are missing:")
        for path in missing:
            print(f"[gate18p]   missing: {path}")
        raise SystemExit(1)

    print("[gate18p] Build vector writer dry-run report")
    run_module(
        "app.scripts.vector_writer_dry_run_validator",
        ["--response-fixture", str(args.response_fixture), "--output", str(args.output)],
        dry_run=args.dry_run,
    )

    print("[gate18p] Validate vector writer dry-run behavior")
    run_module("app.scripts.validate_vector_writer_dry_run", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18p] Dry run complete")
        return

    print("[gate18p] Pipeline complete")
    print("[gate18p] Vector writer validation is dry-run only; vector outputs are not created")


if __name__ == "__main__":
    main()
