from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/apply_numeric_allowlist_dry_run.py",
    "backend/app/scripts/validate_numeric_allowlist_dry_run.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18i]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18I numeric identifier allowlist dry-run checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument(
        "--triage-report",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_redaction_triage_report.v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_numeric_allowlist_dry_run_report.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18i] Starting numeric identifier allowlist dry-run pipeline")
    print(f"[gate18i] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18i] Expected source files are missing:")
        for path in missing:
            print(f"[gate18i]   missing: {path}")
        raise SystemExit(1)

    print("[gate18i] Apply numeric identifier allowlist to dry-run report")
    run_module(
        "app.scripts.apply_numeric_allowlist_dry_run",
        ["--triage-report", str(args.triage_report), "--output", str(args.output)],
        dry_run=args.dry_run,
    )

    print("[gate18i] Validate numeric identifier allowlist dry-run report")
    run_module("app.scripts.validate_numeric_allowlist_dry_run", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate18i] Dry run complete")
        return

    print("[gate18i] Pipeline complete")
    print("[gate18i] Numeric identifier allowlist is applied to dry-run only; unresolved findings remain blocking")


if __name__ == "__main__":
    main()
