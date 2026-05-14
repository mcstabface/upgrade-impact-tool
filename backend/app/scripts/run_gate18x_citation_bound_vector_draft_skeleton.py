from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/citation_bound_vector_draft_skeleton.py",
    "backend/app/scripts/validate_citation_bound_vector_draft_skeleton.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18x]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18X citation-bound vector draft skeleton checks.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--draft-input",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_fixture_vector_draft_input.v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_fixture_vector_draft_skeleton.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()
    print("[gate18x] Starting citation-bound vector draft skeleton pipeline")
    print(f"[gate18x] Repository root: {repository_root}")
    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18x] Expected source files are missing:")
        for path in missing:
            print(f"[gate18x]   missing: {path}")
        raise SystemExit(1)
    print("[gate18x] Build citation-bound vector draft skeleton")
    run_module(
        "app.scripts.citation_bound_vector_draft_skeleton",
        ["--draft-input", str(args.draft_input), "--output", str(args.output)],
        dry_run=args.dry_run,
    )
    print("[gate18x] Validate citation-bound vector draft skeleton")
    run_module("app.scripts.validate_citation_bound_vector_draft_skeleton", [], dry_run=args.dry_run)
    if args.dry_run:
        print("[gate18x] Dry run complete")
        return
    print("[gate18x] Pipeline complete")
    print("[gate18x] Citation-bound vector draft skeleton is ready; no LLM call was performed")


if __name__ == "__main__":
    main()
