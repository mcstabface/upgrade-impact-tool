from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/embedding_submission_adapter.py",
    "backend/app/scripts/validate_embedding_submission_adapter.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18n]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18N embedding submission adapter interface checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument(
        "--request-jsonl",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_full_text_requests.v1.jsonl",
    )
    parser.add_argument(
        "--precondition-report",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_submission_preconditions.v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_submission_adapter_report.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18n] Starting embedding submission adapter interface pipeline")
    print(f"[gate18n] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18n] Expected source files are missing:")
        for path in missing:
            print(f"[gate18n]   missing: {path}")
        raise SystemExit(1)

    print("[gate18n] Build disabled embedding submission adapter report")
    run_module(
        "app.scripts.embedding_submission_adapter",
        [
            "--request-jsonl",
            str(args.request_jsonl),
            "--precondition-report",
            str(args.precondition_report),
            "--adapter",
            "disabled",
            "--output",
            str(args.output),
        ],
        dry_run=args.dry_run,
    )

    print("[gate18n] Validate embedding submission adapter contract")
    run_module("app.scripts.validate_embedding_submission_adapter", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18n] Dry run complete")
        return

    print("[gate18n] Pipeline complete")
    print("[gate18n] Embedding submission adapter interface remains disabled and non-vectorizing")


if __name__ == "__main__":
    main()
