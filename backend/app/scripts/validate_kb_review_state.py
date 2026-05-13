from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root

ALLOWED_DECISIONS = {"UNSET", "ACCEPT", "REJECT", "NEEDS_MORE_EVIDENCE"}
ALLOWED_ACKNOWLEDGEMENTS = {"UNSET", "ACKNOWLEDGED", "NEEDS_MORE_EVIDENCE"}


@dataclass(frozen=True)
class ValidationFailure:
    check: str
    detail: str


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def draft_claim_ids(draft: dict[str, Any]) -> set[str]:
    return {
        claim.get("claim_id")
        for section in draft.get("sections", [])
        for claim in section.get("claims", [])
        if claim.get("claim_id")
    }


def context_evidence_ids(context: dict[str, Any]) -> set[str]:
    return {item.get("evidence_id") for item in context.get("evidence_items", []) if item.get("evidence_id")}


def image_bearing_evidence_ids(context: dict[str, Any]) -> set[str]:
    return {
        item.get("evidence_id")
        for item in context.get("evidence_items", [])
        if item.get("evidence_id") and (item.get("pdf_context_flags") or {}).get("has_images") is True
    }


def validate_review_state(manifest: dict[str, Any], draft: dict[str, Any], context: dict[str, Any], *, require_complete: bool) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    if manifest.get("artifact_type") != "kb_draft_review_manifest":
        failures.append(ValidationFailure("artifact_type", "Expected kb_draft_review_manifest."))
    if manifest.get("schema_version") != "kb_draft_review_manifest.v1":
        failures.append(ValidationFailure("schema_version", "Expected kb_draft_review_manifest.v1."))
    if manifest.get("review_status") not in {"PENDING_REVIEW", "IN_REVIEW", "REVIEW_COMPLETE"}:
        failures.append(ValidationFailure("review_status", f"Unsupported review status: {manifest.get('review_status')!r}."))

    policy = manifest.get("review_policy") or {}
    if policy.get("finalization_allowed") is not False:
        failures.append(ValidationFailure("review_policy.finalization_allowed", "Gate 10 must keep finalization disabled."))

    claim_ids = draft_claim_ids(draft)
    evidence_ids = context_evidence_ids(context)
    image_ids = image_bearing_evidence_ids(context)
    tasks = manifest.get("claim_review_tasks") or []
    gaps = manifest.get("unresolved_gap_tasks") or []

    if len(tasks) != len(claim_ids):
        failures.append(ValidationFailure("claim_review_tasks.count", f"Expected {len(claim_ids)} claim tasks; found {len(tasks)}."))

    seen_claim_ids: set[str] = set()
    for index, task in enumerate(tasks):
        claim_id = task.get("claim_id")
        decision = task.get("reviewer_decision")
        evidence_refs = task.get("evidence_ids") or []
        if claim_id not in claim_ids:
            failures.append(ValidationFailure(f"claim_review_tasks[{index}].claim_id", f"Unknown claim ID: {claim_id}."))
        if claim_id in seen_claim_ids:
            failures.append(ValidationFailure(f"claim_review_tasks[{index}].claim_id", f"Duplicate claim task: {claim_id}."))
        seen_claim_ids.add(claim_id)
        if decision not in ALLOWED_DECISIONS:
            failures.append(ValidationFailure(f"claim_review_tasks[{index}].reviewer_decision", f"Unsupported decision: {decision!r}."))
        if decision == "ACCEPT" and task.get("requires_evidence_review") and not evidence_refs:
            failures.append(
                ValidationFailure(
                    f"claim_review_tasks[{index}].evidence_ids",
                    "Accepted evidence-backed claim has no evidence IDs.",
                )
            )
        for evidence_id in evidence_refs:
            if evidence_id not in evidence_ids:
                failures.append(ValidationFailure(f"claim_review_tasks[{index}].evidence_ids", f"Unknown evidence ID: {evidence_id}."))
        if set(evidence_refs) & image_ids:
            if task.get("requires_visual_review") is not True:
                failures.append(
                    ValidationFailure(
                        f"claim_review_tasks[{index}].requires_visual_review",
                        "Image-bearing evidence task must require visual review.",
                    )
                )
            if decision == "ACCEPT" and task.get("visual_acknowledgement_status") != "ACKNOWLEDGED":
                failures.append(
                    ValidationFailure(
                        f"claim_review_tasks[{index}].visual_acknowledgement_status",
                        "Accepted claim citing image-bearing evidence requires visual acknowledgement.",
                    )
                )
        if decision != "UNSET" and task.get("review_status") != "REVIEWED":
            failures.append(ValidationFailure(f"claim_review_tasks[{index}].review_status", "Reviewed decision must set review_status=REVIEWED."))
        if require_complete and decision == "UNSET":
            failures.append(ValidationFailure(f"claim_review_tasks[{index}].reviewer_decision", "Completion requires every claim decision to be set."))

    expected_gap_count = sum(len(section.get("unresolved_gaps") or []) for section in draft.get("sections", []))
    if len(gaps) != expected_gap_count:
        failures.append(ValidationFailure("unresolved_gap_tasks.count", f"Expected {expected_gap_count} gap tasks; found {len(gaps)}."))
    for index, gap in enumerate(gaps):
        acknowledgement = gap.get("acknowledgement_status")
        if acknowledgement not in ALLOWED_ACKNOWLEDGEMENTS:
            failures.append(
                ValidationFailure(
                    f"unresolved_gap_tasks[{index}].acknowledgement_status",
                    f"Unsupported acknowledgement: {acknowledgement!r}.",
                )
            )
        if acknowledgement != "UNSET" and gap.get("review_status") != "ACKNOWLEDGED":
            failures.append(ValidationFailure(f"unresolved_gap_tasks[{index}].review_status", "Acknowledged gap must set review_status=ACKNOWLEDGED."))
        if require_complete and acknowledgement == "UNSET":
            failures.append(
                ValidationFailure(
                    f"unresolved_gap_tasks[{index}].acknowledgement_status",
                    "Completion requires every unresolved gap to be acknowledged or marked needs-more-evidence.",
                )
            )

    diagnostics = manifest.get("diagnostics") or {}
    if diagnostics.get("accepted_claims") != sum(1 for task in tasks if task.get("reviewer_decision") == "ACCEPT"):
        failures.append(ValidationFailure("diagnostics.accepted_claims", "Accepted claim count mismatch."))
    if diagnostics.get("rejected_claims") != sum(1 for task in tasks if task.get("reviewer_decision") == "REJECT"):
        failures.append(ValidationFailure("diagnostics.rejected_claims", "Rejected claim count mismatch."))
    if diagnostics.get("needs_more_evidence_claims") != sum(1 for task in tasks if task.get("reviewer_decision") == "NEEDS_MORE_EVIDENCE"):
        failures.append(ValidationFailure("diagnostics.needs_more_evidence_claims", "Needs-more-evidence claim count mismatch."))
    if diagnostics.get("acknowledged_gaps") != sum(1 for gap in gaps if gap.get("acknowledgement_status") == "ACKNOWLEDGED"):
        failures.append(ValidationFailure("diagnostics.acknowledged_gaps", "Acknowledged gap count mismatch."))

    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 10 mutable KB draft review state.")
    parser.add_argument("--manifest", type=Path, default=root / "kbs" / "review" / "kb_draft_review_manifest.v1.json")
    parser.add_argument("--draft", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_draft.v1.json")
    parser.add_argument("--context", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_context.v2.enriched.json")
    parser.add_argument("--require-complete", action="store_true", help="Require every decision and gap acknowledgement to be set.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate_review_state(
        read_json(args.manifest),
        read_json(args.draft),
        read_json(args.context),
        require_complete=args.require_complete,
    )
    if failures:
        print("[gate10:validate] FAILED")
        for failure in failures:
            print(f"[gate10:validate] {failure.check}: {failure.detail}")
        raise SystemExit(1)
    print("[gate10:validate] OK")
    print(f"[gate10:validate] manifest={args.manifest}")
    print(f"[gate10:validate] require_complete={args.require_complete}")


if __name__ == "__main__":
    main()
