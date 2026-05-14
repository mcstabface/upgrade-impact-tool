from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.gate18y_local_skeleton_fixture import ensure_local_skeleton_fixture


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/citation_bound_vector_draft_generation_contract.py",
    "backend/app/scripts/validate_citation_bound_vector_draft_generation_contract.py",
    "backend/app/scripts/gate18y_local_skeleton_fixture.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18y]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18Y citation-bound vector draft generation contract checks.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--draft-skeleton",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_fixture_vector_draft_skeleton.v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_fixture_vector_draft_generation_contract.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()
    print("[gate18y] Starting citation-bound vector draft generation contract pipeline")
    print(f"[gate18y] Repository root: {repository_root}")
    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18y] Expected source files are missing:")
        for path in missing:
            print(f"[gate18y]   missing: {path}")
        raise SystemExit(1)
    if not args.dry_run:
        ensure_local_skeleton_fixture(args.draft_skeleton)
    print("[gate18y] Build citation-bound vector draft generation contract")
    run_module(
        "app.scripts.citation_bound_vector_draft_generation_contract",
        ["--draft-skeleton", str(args.draft_skeleton), "--output", str(args.output)],
        dry_run=args.dry_run,
    )
    print("[gate18y] Validate citation-bound vector draft generation contract")
    run_module("app.scripts.validate_citation_bound_vector_draft_generation_contract", [], dry_run=args.dry_run)
    if args.dry_run:
        print("[gate18y] Dry run complete")
        return
    print("[gate18y] Pipeline complete")
    print("[gate18y] Citation-bound vector draft generation contract is ready; generation remains disabled")


if __name__ == "__main__":
    main()
