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
        label="Run constrained KB impact draft pipeline",
        module="app.scripts.run_gate8_kb_impact_draft",
        args=[],
    ),
    PipelineStep(
        label="Build KB draft review manifest",
        module="app.scripts.build_kb_draft_review_manifest",
        args=[],
    ),
    PipelineStep(
        label="Validate KB draft review manifest",
        module="app.scripts.validate_kb_draft_review_manifest",
        args=[],
    ),
    PipelineStep(
        label="Write KB draft review export",
        module="app.scripts.write_kb_draft_review_export",
        args=[],
    ),
]

EXPECTED_OUTPUTS = [
    "kbs/impact_context/kb_impact_draft.v1.json",
    "kbs/review/kb_draft_review_manifest.v1.json",
    "kbs/manifests/kb_draft_review_export.md",
]


def run_step(step: PipelineStep, *, dry_run: bool) -> None:
    command = [sys.executable, "-m", step.module, *step.args]
    print(f"[gate9] {step.label}")
    print(f"[gate9]   {' '.join(command)}")

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
    parser = argparse.ArgumentParser(description="Run Gate 9 KB draft review workflow pipeline.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate9] Starting KB draft review workflow pipeline")
    print(f"[gate9] Repository root: {repository_root}")

    for step in PIPELINE_STEPS:
        run_step(step, dry_run=args.dry_run)

    if args.dry_run:
        print("[gate9] Dry run complete")
        return

    missing_outputs = verify_outputs(repository_root)
    if missing_outputs:
        print("[gate9] Pipeline completed, but expected outputs are missing:")
        for output in missing_outputs:
            print(f"[gate9]   missing: {output}")
        raise SystemExit(1)

    print("[gate9] Pipeline complete")
    print("[gate9] Outputs:")
    for output in EXPECTED_OUTPUTS:
        print(f"[gate9]   {output}")


if __name__ == "__main__":
    main()
