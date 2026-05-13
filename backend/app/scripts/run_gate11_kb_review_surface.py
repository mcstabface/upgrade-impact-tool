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
        label="Run Gate 9 draft review workflow pipeline",
        module="app.scripts.run_gate9_kb_draft_review",
        args=[],
    ),
    PipelineStep(
        label="Write read-only KB draft review static UI surface",
        module="app.scripts.write_kb_draft_review_static_ui",
        args=[],
    ),
    PipelineStep(
        label="Validate read-only KB draft review static UI surface",
        module="app.scripts.validate_kb_draft_review_surface",
        args=[],
    ),
]

EXPECTED_OUTPUTS = [
    "kbs/review/kb_draft_review_manifest.v1.json",
    "kbs/manifests/kb_draft_review_export.md",
    "kbs/manifests/kb_draft_review_surface.html",
]


def run_step(step: PipelineStep, *, dry_run: bool) -> None:
    command = [sys.executable, "-m", step.module, *step.args]
    print(f"[gate11] {step.label}")
    print(f"[gate11]   {' '.join(command)}")

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
    parser = argparse.ArgumentParser(description="Run Gate 11 read-only KB draft review UI surface pipeline.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate11] Starting read-only KB draft review surface pipeline")
    print(f"[gate11] Repository root: {repository_root}")

    for step in PIPELINE_STEPS:
        run_step(step, dry_run=args.dry_run)

    if args.dry_run:
        print("[gate11] Dry run complete")
        return

    missing_outputs = verify_outputs(repository_root)
    if missing_outputs:
        print("[gate11] Pipeline completed, but expected outputs are missing:")
        for output in missing_outputs:
            print(f"[gate11]   missing: {output}")
        raise SystemExit(1)

    print("[gate11] Pipeline complete")
    print("[gate11] Outputs:")
    for output in EXPECTED_OUTPUTS:
        print(f"[gate11]   {output}")


if __name__ == "__main__":
    main()
