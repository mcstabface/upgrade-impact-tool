from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/disabled_adapter_selection_smoke.py",
    "backend/app/scripts/validate_disabled_adapter_selection_smoke.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate17i]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 17I disabled adapter selection smoke checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate17i] Starting disabled adapter selection smoke pipeline")
    print(f"[gate17i] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate17i] Expected source files are missing:")
        for path in missing:
            print(f"[gate17i]   missing: {path}")
        raise SystemExit(1)

    print("[gate17i] Validate disabled adapter selection smoke")
    run_module("app.scripts.validate_disabled_adapter_selection_smoke", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate17i] Dry run complete")
        return

    print("[gate17i] Pipeline complete")
    print("[gate17i] Disabled adapter selection smoke remains non-authorizing and audit-valid")


if __name__ == "__main__":
    main()
