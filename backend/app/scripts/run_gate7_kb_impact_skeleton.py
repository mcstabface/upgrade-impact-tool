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
        label="Assemble Gate 6 KB impact context evidence packet",
        module="app.scripts.assemble_kb_impact_context",
        args=[],
    ),
    PipelineStep(
        label="Enrich KB impact context with PFDS flags and exception context",
        module="app.scripts.enrich_kb_impact_context",
        args=[],
    ),
    PipelineStep(
        label="Build structure-only KB impact draft skeleton",
        module="app.scripts.build_kb_impact_draft_skeleton",
        args=[],
    ),
    PipelineStep(
        label="Validate enriched KB impact context and draft skeleton",
        module="app.scripts.validate_kb_impact_draft_skeleton",
        args=[],
    ),
    PipelineStep(
        label="Write KB impact draft skeleton summary report",
        module="app.scripts.write_kb_impact_draft_skeleton_summary",
        args=[],
    ),
]

EXPECTED_OUTPUTS = [
    "kbs/impact_context/kb_impact_context.v1.json",
    "kbs/impact_context/kb_impact_context.v2.enriched.json",
    "kbs/impact_context/kb_impact_draft_skeleton.v1.json",
    "kbs/manifests/kb_impact_draft_skeleton_summary.md",
]


def run_step(step: PipelineStep, *, dry_run: bool) -> None:
    command = [sys.executable, "-m", step.module, *step.args]
    print(f"[gate7] {step.label}")
    print(f"[gate7]   {' '.join(command)}")

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
    parser = argparse.ArgumentParser(description="Run Gate 7 KB impact context enrichment and draft skeleton pipeline.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate7] Starting KB impact context enrichment pipeline")
    print(f"[gate7] Repository root: {repository_root}")

    for step in PIPELINE_STEPS:
        run_step(step, dry_run=args.dry_run)

    if args.dry_run:
        print("[gate7] Dry run complete")
        return

    missing_outputs = verify_outputs(repository_root)
    if missing_outputs:
        print("[gate7] Pipeline completed, but expected outputs are missing:")
        for output in missing_outputs:
            print(f"[gate7]   missing: {output}")
        raise SystemExit(1)

    print("[gate7] Pipeline complete")
    print("[gate7] Outputs:")
    for output in EXPECTED_OUTPUTS:
        print(f"[gate7]   {output}")


if __name__ == "__main__":
    main()
