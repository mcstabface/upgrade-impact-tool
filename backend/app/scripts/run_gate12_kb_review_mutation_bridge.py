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


ROOT = repo_root()
REVIEW_ROOT = ROOT / "kbs" / "review"
MANIFEST_ROOT = ROOT / "kbs" / "manifests"
BASE_MANIFEST = REVIEW_ROOT / "kb_draft_review_manifest.v1.json"
BRIDGE_MANIFEST = REVIEW_ROOT / "kb_draft_review_manifest.gate12_bridge.json"
BRIDGE_EXPORT = MANIFEST_ROOT / "kb_draft_review_export.gate12_bridge.md"
BRIDGE_SURFACE = MANIFEST_ROOT / "kb_draft_review_surface.gate12_bridge.html"


PIPELINE_STEPS = [
    PipelineStep(
        label="Run Gate 11 read-only review surface pipeline",
        module="app.scripts.run_gate11_kb_review_surface",
        args=[],
    ),
    PipelineStep(
        label="Apply claim decision through Gate 12 bridge",
        module="app.scripts.apply_kb_review_update",
        args=[
            "--manifest",
            str(BRIDGE_MANIFEST),
            "--output",
            str(BRIDGE_MANIFEST),
            "--export-output",
            str(BRIDGE_EXPORT),
            "--surface-output",
            str(BRIDGE_SURFACE),
            "--reviewer",
            "GATE12_SMOKE",
            "--notes",
            "Bridge smoke-test acceptance with visual acknowledgement.",
            "claim",
            "evidence_group_006",
            "ACCEPT",
            "--visual-acknowledged",
        ],
    ),
    PipelineStep(
        label="Apply gap acknowledgement through Gate 12 bridge",
        module="app.scripts.apply_kb_review_update",
        args=[
            "--manifest",
            str(BRIDGE_MANIFEST),
            "--output",
            str(BRIDGE_MANIFEST),
            "--export-output",
            str(BRIDGE_EXPORT),
            "--surface-output",
            str(BRIDGE_SURFACE),
            "--reviewer",
            "GATE12_SMOKE",
            "--notes",
            "Bridge smoke-test unresolved gap acknowledgement.",
            "gap",
            "gap_001",
            "ACKNOWLEDGED",
        ],
    ),
    PipelineStep(
        label="Validate bridged mutable review state",
        module="app.scripts.validate_kb_review_state",
        args=["--manifest", str(BRIDGE_MANIFEST)],
    ),
    PipelineStep(
        label="Validate bridged audit trail",
        module="app.scripts.validate_kb_review_audit_trail",
        args=["--manifest", str(BRIDGE_MANIFEST), "--min-events", "2"],
    ),
    PipelineStep(
        label="Validate bridged read-only review surface",
        module="app.scripts.validate_kb_draft_review_surface",
        args=["--surface", str(BRIDGE_SURFACE)],
    ),
]

EXPECTED_OUTPUTS = [
    "kbs/review/kb_draft_review_manifest.gate12_bridge.json",
    "kbs/manifests/kb_draft_review_export.gate12_bridge.md",
    "kbs/manifests/kb_draft_review_surface.gate12_bridge.html",
]


def run_step(step: PipelineStep, *, dry_run: bool) -> None:
    command = [sys.executable, "-m", step.module, *step.args]
    print(f"[gate12] {step.label}")
    print(f"[gate12]   {' '.join(command)}")

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
    parser = argparse.ArgumentParser(description="Run Gate 12 KB review mutation bridge smoke checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate12] Starting KB review mutation bridge pipeline")
    print(f"[gate12] Repository root: {repository_root}")

    if not args.dry_run:
        REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
        MANIFEST_ROOT.mkdir(parents=True, exist_ok=True)

    for index, step in enumerate(PIPELINE_STEPS):
        if index == 1 and not args.dry_run:
            shutil.copyfile(BASE_MANIFEST, BRIDGE_MANIFEST)
            print(f"[gate12] Copied base manifest to bridge manifest: {BRIDGE_MANIFEST}")
        run_step(step, dry_run=args.dry_run)

    if args.dry_run:
        print("[gate12] Dry run complete")
        return

    missing_outputs = verify_outputs(repository_root)
    if missing_outputs:
        print("[gate12] Pipeline completed, but expected outputs are missing:")
        for output in missing_outputs:
            print(f"[gate12]   missing: {output}")
        raise SystemExit(1)

    print("[gate12] Pipeline complete")
    print("[gate12] Outputs:")
    for output in EXPECTED_OUTPUTS:
        print(f"[gate12]   {output}")


if __name__ == "__main__":
    main()
