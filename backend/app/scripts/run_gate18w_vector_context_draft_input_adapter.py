from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/vector_context_draft_input_adapter.py",
    "backend/app/scripts/validate_vector_context_draft_input_adapter.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18w]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18W vector context draft input adapter checks.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--vector-context",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_fixture_vector_context.v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_fixture_vector_draft_input.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()
    print("[gate18w] Starting vector context draft input adapter pipeline")
    print(f"[gate18w] Repository root: {repository_root}")
    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18w] Expected source files are missing:")
        for path in missing:
            print(f"[gate18w]   missing: {path}")
        raise SystemExit(1)
    print("[gate18w] Adapt vector context to draft input")
    run_module(
        "app.scripts.vector_context_draft_input_adapter",
        ["--vector-context", str(args.vector_context), "--output", str(args.output)],
        dry_run=args.dry_run,
    )
    print("[gate18w] Validate vector context draft input adapter")
    run_module("app.scripts.validate_vector_context_draft_input_adapter", [], dry_run=args.dry_run)
    if args.dry_run:
        print("[gate18w] Dry run complete")
        return
    print("[gate18w] Pipeline complete")
    print("[gate18w] Vector context is adapted to draft input; draft generation remains disabled")


if __name__ == "__main__":
    main()
