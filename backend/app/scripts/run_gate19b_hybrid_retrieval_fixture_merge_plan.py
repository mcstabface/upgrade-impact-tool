from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/hybrid_retrieval_fixture_merge_plan.py",
    "backend/app/scripts/validate_hybrid_retrieval_fixture_merge_plan.py",
    "backend/app/scripts/hybrid_retrieval_design_contract.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate19b]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 19B hybrid retrieval fixture merge plan checks.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--design-contract",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_hybrid_retrieval_design_contract.v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_hybrid_retrieval_fixture_merge_plan.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()
    print("[gate19b] Starting hybrid retrieval fixture merge plan pipeline")
    print(f"[gate19b] Repository root: {repository_root}")
    missing = verify_source_files(repository_root)
    if missing:
        print("[gate19b] Expected source files are missing:")
        for path in missing:
            print(f"[gate19b]   missing: {path}")
        raise SystemExit(1)
    print("[gate19b] Build hybrid retrieval fixture merge plan")
    run_module(
        "app.scripts.hybrid_retrieval_fixture_merge_plan",
        ["--design-contract", str(args.design_contract), "--output", str(args.output)],
        dry_run=args.dry_run,
    )
    print("[gate19b] Validate hybrid retrieval fixture merge plan")
    run_module("app.scripts.validate_hybrid_retrieval_fixture_merge_plan", [], dry_run=args.dry_run)
    if args.dry_run:
        print("[gate19b] Dry run complete")
        return
    print("[gate19b] Pipeline complete")
    print("[gate19b] Hybrid retrieval fixture merge remains plan-only; merged results are not emitted")


if __name__ == "__main__":
    main()
