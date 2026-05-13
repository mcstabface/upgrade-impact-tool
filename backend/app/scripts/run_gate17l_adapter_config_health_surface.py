from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/guarded_review_update_http_server.py",
    "backend/app/scripts/validate_gate17l_adapter_config_health_surface.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate17l]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 17L adapter config read-only health surface checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate17l] Starting adapter config health surface pipeline")
    print(f"[gate17l] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate17l] Expected source files are missing:")
        for path in missing:
            print(f"[gate17l]   missing: {path}")
        raise SystemExit(1)

    print("[gate17l] Validate adapter config health surface")
    run_module("app.scripts.validate_gate17l_adapter_config_health_surface", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate17l] Dry run complete")
        return

    print("[gate17l] Pipeline complete")
    print("[gate17l] Adapter config health surface remains read-only with local-policy live adapter")


if __name__ == "__main__":
    main()
