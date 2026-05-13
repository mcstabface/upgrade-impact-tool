from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/embedding_dry_run_submission_contract.py",
    "backend/app/scripts/validate_embedding_dry_run_submission_contract.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18g]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18G dry-run embedding submission contract checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument(
        "--request-jsonl",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_full_text_requests.v1.jsonl",
    )
    parser.add_argument(
        "--payload-report",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_full_text_payload_report.v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_dry_run_submission_report.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18g] Starting dry-run embedding submission contract pipeline")
    print(f"[gate18g] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18g] Expected source files are missing:")
        for path in missing:
            print(f"[gate18g]   missing: {path}")
        raise SystemExit(1)

    print("[gate18g] Build dry-run embedding submission report")
    run_module(
        "app.scripts.embedding_dry_run_submission_contract",
        [
            "--request-jsonl",
            str(args.request_jsonl),
            "--payload-report",
            str(args.payload_report),
            "--output",
            str(args.output),
        ],
        dry_run=args.dry_run,
    )

    print("[gate18g] Validate dry-run embedding submission contract")
    run_module("app.scripts.validate_embedding_dry_run_submission_contract", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18g] Dry run complete")
        return

    print("[gate18g] Pipeline complete")
    print("[gate18g] Dry-run embedding submission contract remains non-submitting and non-vectorizing")


if __name__ == "__main__":
    main()
