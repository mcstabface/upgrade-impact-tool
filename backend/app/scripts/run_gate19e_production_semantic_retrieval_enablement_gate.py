from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/production_semantic_retrieval_enablement_gate.py",
    "backend/app/scripts/validate_production_semantic_retrieval_enablement_gate.py",
    "backend/app/scripts/hybrid_retrieval_citation_preservation_validator.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate19e]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 19E production semantic retrieval enablement checks.")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--citation-preservation",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_hybrid_retrieval_citation_preservation.v1.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_production_semantic_retrieval_enablement_gate.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()
    print("[gate19e] Starting production semantic retrieval enablement gate pipeline")
    print(f"[gate19e] Repository root: {repository_root}")
    missing = verify_source_files(repository_root)
    if missing:
        print("[gate19e] Expected source files are missing:")
        for path in missing:
            print(f"[gate19e]   missing: {path}")
        raise SystemExit(1)
    print("[gate19e] Build production semantic retrieval enablement report")
    run_module(
        "app.scripts.production_semantic_retrieval_enablement_gate",
        ["--citation-preservation", str(args.citation_preservation), "--output", str(args.output)],
        dry_run=args.dry_run,
    )
    print("[gate19e] Validate production semantic retrieval enablement gate")
    run_module("app.scripts.validate_production_semantic_retrieval_enablement_gate", [], dry_run=args.dry_run)
    if args.dry_run:
        print("[gate19e] Dry run complete")
        return
    print("[gate19e] Pipeline complete")
    print("[gate19e] Production semantic retrieval remains disabled and fail-closed")


if __name__ == "__main__":
    main()
