from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


@dataclass(frozen=True)
class PipelineStep:
    label: str
    module: str


PIPELINE_STEPS = [
    PipelineStep(
        label="Extract KB matched PFDS search context artifacts",
        module="app.scripts.extract_kb_search_context",
    ),
    PipelineStep(
        label="Chunk KB search context artifacts",
        module="app.scripts.chunk_kb_search_context",
    ),
    PipelineStep(
        label="Validate KB search context manifests",
        module="app.scripts.validate_gate2_kb_search_context",
    ),
]

EXPECTED_OUTPUTS = [
    "kbs/manifests/kb_search_context_manifest.json",
    "kbs/manifests/kb_search_context_chunks_manifest.json",
]


def run_step(step: PipelineStep, *, dry_run: bool) -> None:
    command = [sys.executable, "-m", step.module]
    print(f"[gate2] {step.label}")
    print(f"[gate2]   {' '.join(command)}")

    if dry_run:
        return

    subprocess.run(command, check=True)


def verify_outputs(repository_root: Path) -> list[str]:
    missing: list[str] = []
    for output in EXPECTED_OUTPUTS:
        if not (repository_root / output).exists():
            missing.append(output)
    return missing


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the Gate 2 KB source text extraction and search-context artifact pipeline."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the pipeline commands without running them.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate2] Starting KB search context pipeline")
    print(f"[gate2] Repository root: {repository_root}")

    for step in PIPELINE_STEPS:
        run_step(step, dry_run=args.dry_run)

    if args.dry_run:
        print("[gate2] Dry run complete")
        return

    missing_outputs = verify_outputs(repository_root)
    if missing_outputs:
        print("[gate2] Pipeline completed, but expected outputs are missing:")
        for output in missing_outputs:
            print(f"[gate2]   missing: {output}")
        raise SystemExit(1)

    print("[gate2] Pipeline complete")
    print("[gate2] Outputs:")
    for output in EXPECTED_OUTPUTS:
        print(f"[gate2]   {output}")


if __name__ == "__main__":
    main()
