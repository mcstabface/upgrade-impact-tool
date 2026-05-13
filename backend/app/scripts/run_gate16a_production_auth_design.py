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
        label="Validate Gate 16A production auth design spec",
        module="app.scripts.validate_gate16a_production_auth_design",
        args=[],
    ),
]

EXPECTED_OUTPUTS = [
    "docs/security/Gate 16A Production Auth Design Spec.md",
]


def run_step(step: PipelineStep, *, dry_run: bool) -> None:
    command = [sys.executable, "-m", step.module, *step.args]
    print(f"[gate16a] {step.label}")
    print(f"[gate16a]   {' '.join(command)}")
    if not dry_run:
        subprocess.run(command, check=True)


def verify_outputs(repository_root: Path) -> list[str]:
    return [output for output in EXPECTED_OUTPUTS if not (repository_root / output).exists()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 16A production auth design validation.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()
    print("[gate16a] Starting production auth design validation")
    print(f"[gate16a] Repository root: {repository_root}")
    for step in PIPELINE_STEPS:
        run_step(step, dry_run=args.dry_run)
    if args.dry_run:
        print("[gate16a] Dry run complete")
        return
    missing_outputs = verify_outputs(repository_root)
    if missing_outputs:
        print("[gate16a] Validation completed, but expected outputs are missing:")
        for output in missing_outputs:
            print(f"[gate16a]   missing: {output}")
        raise SystemExit(1)
    print("[gate16a] Pipeline complete")
    print("[gate16a] Outputs:")
    for output in EXPECTED_OUTPUTS:
        print(f"[gate16a]   {output}")


if __name__ == "__main__":
    main()
