from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/disabled_vector_draft_generator_adapter.py",
    "backend/app/scripts/validate_disabled_vector_draft_generator_adapter.py",
    "backend/app/scripts/gate18y_local_skeleton_fixture.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18z]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18Z disabled vector draft generator adapter checks.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--generation-contract",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_fixture_vector_draft_generation_contract.v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_fixture_vector_disabled_generator.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()
    print("[gate18z] Starting disabled vector draft generator adapter pipeline")
    print(f"[gate18z] Repository root: {repository_root}")
    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18z] Expected source files are missing:")
        for path in missing:
            print(f"[gate18z]   missing: {path}")
        raise SystemExit(1)
    print("[gate18z] Run disabled vector draft generator adapter")
    run_module(
        "app.scripts.disabled_vector_draft_generator_adapter",
        ["--generation-contract", str(args.generation_contract), "--adapter", "disabled", "--output", str(args.output)],
        dry_run=args.dry_run,
    )
    print("[gate18z] Validate disabled vector draft generator adapter")
    run_module("app.scripts.validate_disabled_vector_draft_generator_adapter", [], dry_run=args.dry_run)
    if args.dry_run:
        print("[gate18z] Dry run complete")
        return
    print("[gate18z] Pipeline complete")
    print("[gate18z] Disabled vector draft generator refuses generation; no LLM call was performed")


if __name__ == "__main__":
    main()
