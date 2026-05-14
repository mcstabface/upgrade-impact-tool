from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/vector_writer_commit_gate_design.py",
    "backend/app/scripts/validate_vector_writer_commit_gate_design.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18q]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18Q vector writer commit gate design checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument(
        "--dry-run-report",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_vector_writer_dry_run_report.v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_vector_writer_commit_gate.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18q] Starting vector writer commit gate design pipeline")
    print(f"[gate18q] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18q] Expected source files are missing:")
        for path in missing:
            print(f"[gate18q]   missing: {path}")
        raise SystemExit(1)

    print("[gate18q] Build vector writer commit gate report")
    run_module(
        "app.scripts.vector_writer_commit_gate_design",
        ["--dry-run-report", str(args.dry_run_report), "--output", str(args.output)],
        dry_run=args.dry_run,
    )

    print("[gate18q] Validate vector writer commit gate design")
    run_module("app.scripts.validate_vector_writer_commit_gate_design", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18q] Dry run complete")
        return

    print("[gate18q] Pipeline complete")
    print("[gate18q] Vector writer commit gate is ready but disabled; vectors are not created")


if __name__ == "__main__":
    main()
