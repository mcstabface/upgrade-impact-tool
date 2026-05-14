from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/export_unresolved_redaction_review.py",
    "backend/app/scripts/validate_unresolved_redaction_review_export.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18j]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18J unresolved redaction finding review export checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument(
        "--triage-report",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_redaction_triage_report.v1.json",
    )
    parser.add_argument(
        "--request-jsonl",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_full_text_requests.v1.jsonl",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_unresolved_redaction_review.v1.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_unresolved_redaction_review.v1.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18j] Starting unresolved redaction finding review export pipeline")
    print(f"[gate18j] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18j] Expected source files are missing:")
        for path in missing:
            print(f"[gate18j]   missing: {path}")
        raise SystemExit(1)

    print("[gate18j] Export unresolved redaction findings for review")
    run_module(
        "app.scripts.export_unresolved_redaction_review",
        [
            "--triage-report",
            str(args.triage_report),
            "--request-jsonl",
            str(args.request_jsonl),
            "--json-output",
            str(args.json_output),
            "--markdown-output",
            str(args.markdown_output),
        ],
        dry_run=args.dry_run,
    )

    print("[gate18j] Validate unresolved redaction review export")
    run_module("app.scripts.validate_unresolved_redaction_review_export", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18j] Dry run complete")
        return

    print("[gate18j] Pipeline complete")
    print("[gate18j] Unresolved redaction findings are exported for review; embedding submission remains forbidden")


if __name__ == "__main__":
    main()
