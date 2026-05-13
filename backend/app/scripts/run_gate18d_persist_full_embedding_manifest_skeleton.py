from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


EXPECTED_SOURCE_FILES = [
    "backend/app/scripts/build_embedding_manifest_from_chunks.py",
    "backend/app/scripts/validate_persisted_embedding_manifest_skeleton.py",
]


def run_module(module: str, args: list[str], *, dry_run: bool) -> None:
    command = [sys.executable, "-m", module, *args]
    print(f"[gate18d]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_source_files(repository_root: Path) -> list[str]:
    return [path for path in EXPECTED_SOURCE_FILES if not (repository_root / path).exists()]


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18D full embedding manifest skeleton persistence.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument(
        "--source-chunk-manifest",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_search_context_chunks_manifest.json",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "retrieval" / "kb_embedding_manifest.v1.json",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate18d] Starting full embedding manifest skeleton persistence pipeline")
    print(f"[gate18d] Repository root: {repository_root}")

    missing = verify_source_files(repository_root)
    if missing:
        print("[gate18d] Expected source files are missing:")
        for path in missing:
            print(f"[gate18d]   missing: {path}")
        raise SystemExit(1)

    print("[gate18d] Build full embedding manifest skeleton")
    run_module(
        "app.scripts.build_embedding_manifest_from_chunks",
        ["--source-chunk-manifest", str(args.source_chunk_manifest), "--output", str(args.output)],
        dry_run=args.dry_run,
    )

    print("[gate18d] Validate persisted embedding manifest skeleton")
    run_module(
        "app.scripts.validate_persisted_embedding_manifest_skeleton",
        ["--manifest", str(args.output), "--source-chunk-manifest", str(args.source_chunk_manifest)],
        dry_run=args.dry_run,
    )

    if args.dry_run:
        print("[gate18d] Dry run complete")
        return

    print("[gate18d] Pipeline complete")
    print("[gate18d] Full embedding manifest skeleton persists without vector creation")


if __name__ == "__main__":
    main()
