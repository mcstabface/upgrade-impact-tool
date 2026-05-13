from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/embedding_full_text_payload_plan.py",
    "backend/app/scripts/validate_embedding_full_text_payload_plan.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18f]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18F full-text request payload and redaction checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument("--manifest", type=Path, default=root / "kbs" / "retrieval" / "kb_embedding_manifest.v1.json")
    parser.add_argument(
        "--source-chunk-manifest",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_search_context_chunks_manifest.json",
    )
    parser.add_argument(
        "--request-jsonl-output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_full_text_requests.v1.jsonl",
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_full_text_payload_report.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18f] Starting full-text embedding payload redaction pipeline")
    print(f"[gate18f] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18f] Expected source files are missing:")
        for path in missing:
            print(f"[gate18f]   missing: {path}")
        raise SystemExit(1)

    print("[gate18f] Build full-text embedding request payloads")
    run_module(
        "app.scripts.embedding_full_text_payload_plan",
        [
            "--manifest",
            str(args.manifest),
            "--source-chunk-manifest",
            str(args.source_chunk_manifest),
            "--request-jsonl-output",
            str(args.request_jsonl_output),
            "--report-output",
            str(args.report_output),
        ],
        dry_run=args.dry_run,
    )

    print("[gate18f] Validate full-text embedding payload plan")
    run_module("app.scripts.validate_embedding_full_text_payload_plan", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18f] Dry run complete")
        return

    print("[gate18f] Pipeline complete")
    print("[gate18f] Full-text embedding payloads are ready but not submitted")


if __name__ == "__main__":
    main()
