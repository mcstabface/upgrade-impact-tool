from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/citation_bound_vector_context_assembly.py",
    "backend/app/scripts/validate_citation_bound_vector_context.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18v]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18V citation-bound vector context assembly checks.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--citation-join-report", type=Path, default=root / "kbs" / "retrieval" / "kb_fixture_vector_citation_join.v1.json")
    parser.add_argument("--output", type=Path, default=root / "kbs" / "retrieval" / "kb_fixture_vector_context.v1.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()
    print("[gate18v] Starting citation-bound vector context assembly pipeline")
    print(f"[gate18v] Repository root: {repository_root}")
    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18v] Expected source files are missing:")
        for path in missing:
            print(f"[gate18v]   missing: {path}")
        raise SystemExit(1)
    print("[gate18v] Assemble citation-bound vector context")
    run_module(
        "app.scripts.citation_bound_vector_context_assembly",
        ["--citation-join-report", str(args.citation_join_report), "--output", str(args.output)],
        dry_run=args.dry_run,
    )
    print("[gate18v] Validate citation-bound vector context")
    run_module("app.scripts.validate_citation_bound_vector_context", [], dry_run=args.dry_run)
    if args.dry_run:
        print("[gate18v] Dry run complete")
        return
    print("[gate18v] Pipeline complete")
    print("[gate18v] Citation-bound vector context is assembled; impact generation remains disabled")


if __name__ == "__main__":
    main()
