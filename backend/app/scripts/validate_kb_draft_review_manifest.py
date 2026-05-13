from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


@dataclass(frozen=True)
class ValidationFailure:
    check: str
    detail: str


def read_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_manifest(manifest: dict, draft: dict, context: dict) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    if manifest.get("artifact_type") != "kb_draft_review_manifest":
        failures.append(ValidationFailure("artifact_type", "Expected kb_draft_review_manifest."))
    if manifest.get("schema_version") != "kb_draft_review_manifest.v1":
        failures.append(ValidationFailure("schema_version", "Expected kb_draft_review_manifest.v1."))
    if manifest.get("review_status") != "PENDING_REVIEW":
        failures.append(ValidationFailure("review_status", "Initial review manifest must be PENDING_REVIEW."))

    policy = manifest.get("review_policy") or {}
    expected = {
        "claims_default_to_pending": True,
        "accepted_claims_require_evidence_ids": True,
        "image_bearing_claims_require_visual_acknowledgement": True,
        "unresolved_gaps_require_acknowledgement": True,
        "finalization_allowed": False,
    }
    for field, expected_value in expected.items():
        if policy.get(field) is not expected_value:
            failures.append(ValidationFailure(f"review_policy.{field}", f"Expected {expected_value!r}; found {policy.get(field)!r}."))

    allowed_decisions = set(policy.get("reviewer_decisions_allowed") or [])
    if not {"UNSET", "ACCEPT", "REJECT", "NEEDS_MORE_EVIDENCE"}.issubset(allowed_decisions):
        failures.append(ValidationFailure("review_policy.reviewer_decisions_allowed", "Missing required reviewer decisions."))

    draft_claim_ids = {
        claim.get("claim_id")
        for section in draft.get("sections", [])
        for claim in section.get("claims", [])
        if claim.get("claim_id")
    }
    evidence_ids = {item.get("evidence_id") for item in context.get("evidence_items", []) if item.get("evidence_id")}
    image_bearing_ids = {
        item.get("evidence_id")
        for item in context.get("evidence_items", [])
        if item.get("evidence_id") and (item.get("pdf_context_flags") or {}).get("has_images") is True
    }

    tasks = manifest.get("claim_review_tasks") or []
    if len(tasks) != len(draft_claim_ids):
        failures.append(ValidationFailure("claim_review_tasks.count", f"Expected {len(draft_claim_ids)} claim tasks; found {len(tasks)}."))

    seen_claims: set[str] = set()
    for index, task in enumerate(tasks):
        claim_id = task.get("claim_id")
        if claim_id not in draft_claim_ids:
            failures.append(ValidationFailure(f"claim_review_tasks[{index}].claim_id", f"Unknown draft claim ID: {claim_id}."))
        if claim_id in seen_claims:
            failures.append(ValidationFailure(f"claim_review_tasks[{index}].claim_id", f"Duplicate claim task: {claim_id}."))
        seen_claims.add(claim_id)
        if task.get("review_status") != "PENDING_REVIEW":
            failures.append(ValidationFailure(f"claim_review_tasks[{index}].review_status", "Expected PENDING_REVIEW."))
        if task.get("reviewer_decision") != "UNSET":
            failures.append(ValidationFailure(f"claim_review_tasks[{index}].reviewer_decision", "Expected UNSET."))
        evidence_refs = task.get("evidence_ids") or []
        for evidence_id in evidence_refs:
            if evidence_id not in evidence_ids:
                failures.append(ValidationFailure(f"claim_review_tasks[{index}].evidence_ids", f"Unknown evidence ID: {evidence_id}."))
        if evidence_refs and task.get("requires_evidence_review") is not True:
            failures.append(ValidationFailure(f"claim_review_tasks[{index}].requires_evidence_review", "Evidence-backed task must require evidence review."))
        if set(evidence_refs) & image_bearing_ids and task.get("requires_visual_review") is not True:
            failures.append(ValidationFailure(f"claim_review_tasks[{index}].requires_visual_review", "Image-bearing evidence task must require visual review."))

    expected_gap_count = sum(len(section.get("unresolved_gaps") or []) for section in draft.get("sections", []))
    gap_tasks = manifest.get("unresolved_gap_tasks") or []
    if len(gap_tasks) != expected_gap_count:
        failures.append(ValidationFailure("unresolved_gap_tasks.count", f"Expected {expected_gap_count} gap tasks; found {len(gap_tasks)}."))
    for index, task in enumerate(gap_tasks):
        if task.get("review_status") != "PENDING_ACKNOWLEDGEMENT":
            failures.append(ValidationFailure(f"unresolved_gap_tasks[{index}].review_status", "Expected PENDING_ACKNOWLEDGEMENT."))
        if task.get("acknowledgement_status") != "UNSET":
            failures.append(ValidationFailure(f"unresolved_gap_tasks[{index}].acknowledgement_status", "Expected UNSET."))
        if not task.get("gap_text"):
            failures.append(ValidationFailure(f"unresolved_gap_tasks[{index}].gap_text", "Gap text is empty."))

    diagnostics = manifest.get("diagnostics") or {}
    if diagnostics.get("claim_review_tasks") != len(tasks):
        failures.append(ValidationFailure("diagnostics.claim_review_tasks", "Diagnostic count does not match claim task count."))
    if diagnostics.get("visual_review_tasks") != sum(1 for task in tasks if task.get("requires_visual_review")):
        failures.append(ValidationFailure("diagnostics.visual_review_tasks", "Diagnostic count does not match visual-review task count."))
    if diagnostics.get("unresolved_gap_tasks") != len(gap_tasks):
        failures.append(ValidationFailure("diagnostics.unresolved_gap_tasks", "Diagnostic count does not match gap task count."))

    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 9 KB draft review manifest.")
    parser.add_argument("--manifest", type=Path, default=root / "kbs" / "review" / "kb_draft_review_manifest.v1.json")
    parser.add_argument("--draft", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_draft.v1.json")
    parser.add_argument("--context", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_context.v2.enriched.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate_manifest(read_json(args.manifest), read_json(args.draft), read_json(args.context))
    if failures:
        print("[gate9:validate] FAILED")
        for failure in failures:
            print(f"[gate9:validate] {failure.check}: {failure.detail}")
        raise SystemExit(1)
    print("[gate9:validate] OK")
    print(f"[gate9:validate] manifest={args.manifest}")


if __name__ == "__main__":
    main()
