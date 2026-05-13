from __future__ import annotations

import argparse
import shutil
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


REVIEW_ROOT = repo_root() / "kbs" / "review"
BASE_MANIFEST = REVIEW_ROOT / "kb_draft_review_manifest.v1.json"
SMOKE_MANIFEST = REVIEW_ROOT / "kb_draft_review_manifest.gate10_smoke.json"


PIPELINE_STEPS = [
    PipelineStep(
        label="Run Gate 9 draft review workflow pipeline",
        module="app.scripts.run_gate9_kb_draft_review",
        args=[],
    ),
    PipelineStep(
        label="Validate initial mutable review state",
        module="app.scripts.validate_kb_review_state",
        args=["--manifest", str(BASE_MANIFEST)],
    ),
    PipelineStep(
        label="Accept one image-bearing claim with visual acknowledgement",
        module="app.scripts.update_kb_review_claim_decision",
        args=[
            "evidence_group_006",
            "ACCEPT",
            "--manifest",
            str(SMOKE_MANIFEST),
            "--output",
            str(SMOKE_MANIFEST),
            "--reviewer",
            "GATE10_SMOKE",
            "--notes",
            "Smoke-test acceptance with visual acknowledgement.",
            "--visual-acknowledged",
        ],
    ),
    PipelineStep(
        label="Acknowledge one unresolved evidence gap",
        module="app.scripts.update_kb_review_gap_acknowledgement",
        args=[
            "gap_001",
            "ACKNOWLEDGED",
            "--manifest",
            str(SMOKE_MANIFEST),
            "--output",
            str(SMOKE_MANIFEST),
            "--reviewer",
            "GATE10_SMOKE",
            "--notes",
            "Smoke-test unresolved gap acknowledgement.",
        ],
    ),
    PipelineStep(
        label="Validate updated mutable review state",
        module="app.scripts.validate_kb_review_state",
        args=["--manifest", str(SMOKE_MANIFEST)],
    ),
]

EXPECTED_OUTPUTS = [
    "kbs/review/kb_draft_review_manifest.v1.json",
    "kbs/review/kb_draft_review_manifest.gate10_smoke.json",
    "kbs/manifests/kb_draft_review_export.md",
]


def run_step(step: PipelineStep, *, dry_run: bool) -> None:
    command = [sys.executable, "-m", step.module, *step.args]
    print(f"[gate10] {step.label}")
    print(f"[gate10]   {' '.join(command)}")

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
    parser = argparse.ArgumentParser(description="Run Gate 10 KB review decision update smoke checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate10] Starting KB review update smoke pipeline")
    print(f"[gate10] Repository root: {repository_root}")

    if not args.dry_run:
        REVIEW_ROOT.mkdir(parents=True, exist_ok=True)

    for index, step in enumerate(PIPELINE_STEPS):
        if index == 2 and not args.dry_run:
            shutil.copyfile(BASE_MANIFEST, SMOKE_MANIFEST)
            print(f"[gate10] Copied base manifest to smoke manifest: {SMOKE_MANIFEST}")
        run_step(step, dry_run=args.dry_run)

    if args.dry_run:
        print("[gate10] Dry run complete")
        return

    missing_outputs = verify_outputs(repository_root)
    if missing_outputs:
        print("[gate10] Pipeline completed, but expected outputs are missing:")
        for output in missing_outputs:
            print(f"[gate10]   missing: {output}")
        raise SystemExit(1)

    print("[gate10] Pipeline complete")
    print("[gate10] Outputs:")
    for output in EXPECTED_OUTPUTS:
        print(f"[gate10]   {output}")


if __name__ == "__main__":
    main()
