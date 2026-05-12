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
    args: list[str]


PIPELINE_STEPS = [
    PipelineStep(
        label="Assemble KB impact context evidence packet",
        module="app.scripts.assemble_kb_impact_context",
        args=[],
    ),
    PipelineStep(
        label="Validate KB impact context evidence packet",
        module="app.scripts.validate_kb_impact_context",
        args=[],
    ),
    PipelineStep(
        label="Write KB impact context summary report",
        module="app.scripts.write_kb_impact_context_summary",
        args=[],
    ),
]

EXPECTED_OUTPUTS = [
    "kbs/impact_context/kb_impact_context.v1.json",
    "kbs/manifests/kb_impact_context_summary.md",
]


def run_step(step: PipelineStep, *, dry_run: bool) -> None:
    command = [sys.executable, "-m", step.module, *step.args]
    print(f"[gate6] {step.label}")
    print(f"[gate6]   {' '.join(command)}")

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
    parser = argparse.ArgumentParser(description="Run Gate 6 KB impact context assembly pipeline.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate6] Starting KB impact context assembly pipeline")
    print(f"[gate6] Repository root: {repository_root}")

    for step in PIPELINE_STEPS:
        run_step(step, dry_run=args.dry_run)

    if args.dry_run:
        print("[gate6] Dry run complete")
        return

    missing_outputs = verify_outputs(repository_root)
    if missing_outputs:
        print("[gate6] Pipeline completed, but expected outputs are missing:")
        for output in missing_outputs:
            print(f"[gate6]   missing: {output}")
        raise SystemExit(1)

    print("[gate6] Pipeline complete")
    print("[gate6] Outputs:")
    for output in EXPECTED_OUTPUTS:
        print(f"[gate6]   {output}")


if __name__ == "__main__":
    main()
