from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "docs/checkpoints/Gate 17E OIDC JWKS Validation Design Spec.md",
    "backend/app/scripts/validate_gate17e_oidc_jwks_design_spec.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate17e]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 17E OIDC JWKS validation design-spec checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate17e] Starting OIDC JWKS validation design-spec pipeline")
    print(f"[gate17e] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate17e] Expected source files are missing:")
        for path in missing:
            print(f"[gate17e]   missing: {path}")
        raise SystemExit(1)

    print("[gate17e] Validate OIDC JWKS validation design spec")
    run_module("app.scripts.validate_gate17e_oidc_jwks_design_spec", [], dry_run=args.dry_run)

    if args.dry_run:
        print("[gate17e] Dry run complete")
        return

    print("[gate17e] Pipeline complete")
    print("[gate17e] OIDC JWKS validation remains specified but not implemented")


if __name__ == "__main__":
    main()
