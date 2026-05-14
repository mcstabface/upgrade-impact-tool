from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/retrieval_runtime_adapter_boundary.py",
    "backend/app/scripts/validate_retrieval_runtime_adapter_boundary.py",
    "backend/app/scripts/production_semantic_retrieval_enablement_gate.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate20a]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 20A retrieval runtime adapter boundary checks.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--enablement-report",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_production_semantic_retrieval_enablement_gate.v1.json",
    )
    parser.add_argument("--requested-adapter", default="bm25_authoritative")
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_retrieval_runtime_adapter_boundary.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()
    print("[gate20a] Starting retrieval runtime adapter boundary pipeline")
    print(f"[gate20a] Repository root: {repository_root}")
    missing = verify_source_files(repository_root)
    if missing:
        print("[gate20a] Expected source files are missing:")
        for path in missing:
            print(f"[gate20a]   missing: {path}")
        raise SystemExit(1)
    print("[gate20a] Build retrieval runtime adapter boundary")
    run_module(
        "app.scripts.retrieval_runtime_adapter_boundary",
        [
            "--enablement-report",
            str(args.enablement_report),
            "--requested-adapter",
            args.requested_adapter,
            "--output",
            str(args.output),
        ],
        dry_run=args.dry_run,
    )
    print("[gate20a] Validate retrieval runtime adapter boundary")
    run_module("app.scripts.validate_retrieval_runtime_adapter_boundary", [], dry_run=args.dry_run)
    if args.dry_run:
        print("[gate20a] Dry run complete")
        return
    print("[gate20a] Pipeline complete")
    print("[gate20a] Retrieval runtime boundary preserves BM25 authority and refuses semantic adapters")


if __name__ == "__main__":
    main()
