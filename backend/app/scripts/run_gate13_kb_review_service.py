from __future__ import annotations

import argparse
import json
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
SERVICE_MANIFEST = REVIEW_ROOT / "kb_draft_review_manifest.gate13_service.json"
CLAIM_REQUEST = REVIEW_ROOT / "gate13_claim_request.json"
GAP_REQUEST = REVIEW_ROOT / "gate13_gap_request.json"
CLAIM_RESPONSE = REVIEW_ROOT / "gate13_claim_response.json"
GAP_RESPONSE = REVIEW_ROOT / "gate13_gap_response.json"
SERVICE_EXPORT = MANIFEST_ROOT / "kb_draft_review_export.gate13_service.md"
SERVICE_SURFACE = MANIFEST_ROOT / "kb_draft_review_surface.gate13_service.html"


PIPELINE_STEPS = [
    PipelineStep(
        label="Run Gate 11 read-only review surface pipeline",
        module="app.scripts.run_gate11_kb_review_surface",
        args=[],
    ),
    PipelineStep(
        label="Apply claim update through Gate 13 service contract",
        module="app.scripts.apply_kb_review_update_service_request",
        args=[
            str(CLAIM_REQUEST),
            "--manifest",
            str(SERVICE_MANIFEST),
            "--output",
            str(SERVICE_MANIFEST),
            "--export-output",
            str(SERVICE_EXPORT),
            "--surface-output",
            str(SERVICE_SURFACE),
            "--response-output",
            str(CLAIM_RESPONSE),
        ],
    ),
    PipelineStep(
        label="Validate claim update service response",
        module="app.scripts.validate_kb_review_update_service_response",
        args=[
            str(CLAIM_RESPONSE),
            "--expected-action",
            "claim",
            "--expected-target-id",
            "evidence_group_006",
            "--min-audit-events",
            "1",
        ],
    ),
    PipelineStep(
        label="Apply gap update through Gate 13 service contract",
        module="app.scripts.apply_kb_review_update_service_request",
        args=[
            str(GAP_REQUEST),
            "--manifest",
            str(SERVICE_MANIFEST),
            "--output",
            str(SERVICE_MANIFEST),
            "--export-output",
            str(SERVICE_EXPORT),
            "--surface-output",
            str(SERVICE_SURFACE),
            "--response-output",
            str(GAP_RESPONSE),
        ],
    ),
    PipelineStep(
        label="Validate gap update service response",
        module="app.scripts.validate_kb_review_update_service_response",
        args=[
            str(GAP_RESPONSE),
            "--expected-action",
            "gap",
            "--expected-target-id",
            "gap_001",
            "--min-audit-events",
            "2",
        ],
    ),
    PipelineStep(
        label="Validate service mutable review state",
        module="app.scripts.validate_kb_review_state",
        args=["--manifest", str(SERVICE_MANIFEST)],
    ),
    PipelineStep(
        label="Validate service audit trail",
        module="app.scripts.validate_kb_review_audit_trail",
        args=["--manifest", str(SERVICE_MANIFEST), "--min-events", "2"],
    ),
    PipelineStep(
        label="Validate service regenerated read-only surface",
        module="app.scripts.validate_kb_draft_review_surface",
        args=["--surface", str(SERVICE_SURFACE)],
    ),
]

EXPECTED_OUTPUTS = [
    "kbs/review/kb_draft_review_manifest.gate13_service.json",
    "kbs/review/gate13_claim_request.json",
    "kbs/review/gate13_gap_request.json",
    "kbs/review/gate13_claim_response.json",
    "kbs/review/gate13_gap_response.json",
    "kbs/manifests/kb_draft_review_export.gate13_service.md",
    "kbs/manifests/kb_draft_review_surface.gate13_service.html",
]


def write_request_payloads() -> None:
    REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
    CLAIM_REQUEST.write_text(
        json.dumps(
            {
                "action": "claim",
                "target_id": "evidence_group_006",
                "value": "ACCEPT",
                "reviewer": "GATE13_SERVICE_SMOKE",
                "notes": "Service smoke-test acceptance with visual acknowledgement.",
                "visual_acknowledged": True,
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    GAP_REQUEST.write_text(
        json.dumps(
            {
                "action": "gap",
                "target_id": "gap_001",
                "value": "ACKNOWLEDGED",
                "reviewer": "GATE13_SERVICE_SMOKE",
                "notes": "Service smoke-test unresolved gap acknowledgement.",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )


def run_step(step: PipelineStep, *, dry_run: bool) -> None:
    command = [sys.executable, "-m", step.module, *step.args]
    print(f"[gate13] {step.label}")
    print(f"[gate13]   {' '.join(command)}")

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
    parser = argparse.ArgumentParser(description="Run Gate 13 KB review update service smoke checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate13] Starting KB review service pipeline")
    print(f"[gate13] Repository root: {repository_root}")

    if not args.dry_run:
        REVIEW_ROOT.mkdir(parents=True, exist_ok=True)
        MANIFEST_ROOT.mkdir(parents=True, exist_ok=True)
        write_request_payloads()

    for index, step in enumerate(PIPELINE_STEPS):
        if index == 1 and not args.dry_run:
            shutil.copyfile(BASE_MANIFEST, SERVICE_MANIFEST)
            print(f"[gate13] Copied base manifest to service manifest: {SERVICE_MANIFEST}")
        run_step(step, dry_run=args.dry_run)

    if args.dry_run:
        print("[gate13] Dry run complete")
        return

    missing_outputs = verify_outputs(repository_root)
    if missing_outputs:
        print("[gate13] Pipeline completed, but expected outputs are missing:")
        for output in missing_outputs:
            print(f"[gate13]   missing: {output}")
        raise SystemExit(1)

    print("[gate13] Pipeline complete")
    print("[gate13] Outputs:")
    for output in EXPECTED_OUTPUTS:
        print(f"[gate13]   {output}")


if __name__ == "__main__":
    main()
