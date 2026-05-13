from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/embedding_batch_request_plan.py",
    "backend/app/scripts/validate_embedding_batch_request_plan.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18e]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18E embedding batch request plan checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument("--manifest", type=Path, default=root / "kbs" / "retrieval" / "kb_embedding_manifest.v1.json")
    parser.add_argument("--plan-output", type=Path, default=root / "kbs" / "retrieval" / "kb_embedding_batch_request_plan.v1.json")
    parser.add_argument("--request-jsonl-output", type=Path, default=root / "kbs" / "retrieval" / "kb_embedding_batch_requests.v1.jsonl")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18e] Starting embedding batch request plan pipeline")
    print(f"[gate18e] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18e] Expected source files are missing:")
        for path in missing:
            print(f"[gate18e]   missing: {path}")
        raise SystemExit(1)

    print("[gate18e] Build embedding batch request plan")
    run_module(
        "app.scripts.embedding_batch_request_plan",
        ["--manifest", str(args.manifest), "--plan-output", str(args.plan_output), "--request-jsonl-output", str(args.request_jsonl_output)],
        dry_run=args.dry_run,
    )

    print("[gate18e] Validate embedding batch request plan")
    run_module("app.scripts.validate_embedding_batch_request_plan", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18e] Dry run complete")
        return

    print("[gate18e] Pipeline complete")
    print("[gate18e] Embedding batch request plan is ready but not submitted")


if __name__ == "__main__":
    main()
