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
        label="Build source inventory manifest",
        module="app.scripts.extract_kb_source_manifest",
    ),
    PipelineStep(
        label="Extract PDF portfolio attachments",
        module="app.scripts.extract_pdf_portfolios",
    ),
    PipelineStep(
        label="Extract KB fix rows",
        module="app.scripts.extract_kb_fix_rows",
    ),
    PipelineStep(
        label="Build KB evidence map",
        module="app.scripts.build_kb_evidence_map",
    ),
    PipelineStep(
        label="Summarize KB evidence exceptions",
        module="app.scripts.summarize_kb_evidence_exceptions",
    ),
    PipelineStep(
        label="Export KB evidence exceptions CSV",
        module="app.scripts.export_kb_evidence_exceptions_csv",
    ),
    PipelineStep(
        label="Write KB evidence exception summary report",
        module="app.scripts.write_kb_evidence_summary",
    ),
]

EXPECTED_OUTPUTS = [
    "kbs/manifests/source_inventory.json",
    "kbs/manifests/portfolio_extraction.json",
    "kbs/manifests/kb_fix_rows.json",
    "kbs/manifests/kb_evidence_map.json",
    "kbs/manifests/kb_evidence_exceptions.json",
    "kbs/manifests/kb_evidence_exceptions.csv",
    "kbs/manifests/kb_evidence_exception_summary.md",
]


def run_step(step: PipelineStep, *, dry_run: bool) -> None:
    command = [sys.executable, "-m", step.module]
    print(f"[gate1] {step.label}")
    print(f"[gate1]   {' '.join(command)}")

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
        description="Run the Gate 1 KB source extraction, evidence mapping, and reviewer artifact pipeline."
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

    print("[gate1] Starting KB extraction pipeline")
    print(f"[gate1] Repository root: {repository_root}")

    for step in PIPELINE_STEPS:
        run_step(step, dry_run=args.dry_run)

    if args.dry_run:
        print("[gate1] Dry run complete")
        return

    missing_outputs = verify_outputs(repository_root)
    if missing_outputs:
        print("[gate1] Pipeline completed, but expected outputs are missing:")
        for output in missing_outputs:
            print(f"[gate1]   missing: {output}")
        raise SystemExit(1)

    print("[gate1] Pipeline complete")
    print("[gate1] Outputs:")
    for output in EXPECTED_OUTPUTS:
        print(f"[gate1]   {output}")


if __name__ == "__main__":
    main()
