from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import relpath, repo_root


@dataclass(frozen=True)
class ReviewClaimTask:
    claim_id: str
    section_id: str
    claim_type: str
    review_status: str
    evidence_ids: list[str]
    requires_evidence_review: bool
    requires_visual_review: bool
    reviewer_decision: str
    reviewer_notes: str


@dataclass(frozen=True)
class ReviewGapTask:
    gap_id: str
    review_status: str
    gap_text: str
    acknowledgement_status: str
    reviewer_notes: str


@dataclass(frozen=True)
class KBDraftReviewManifest:
    artifact_type: str
    schema_version: str
    generated_utc: str
    review_status: str
    source_draft_path: str
    source_context_path: str
    review_policy: dict[str, Any]
    diagnostics: dict[str, Any]
    claim_review_tasks: list[ReviewClaimTask] = field(default_factory=list)
    unresolved_gap_tasks: list[ReviewGapTask] = field(default_factory=list)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def evidence_lookup(context: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["evidence_id"]: item for item in context.get("evidence_items", []) if item.get("evidence_id")}


def claim_requires_visual_review(evidence_ids: list[str], evidence_by_id: dict[str, dict[str, Any]]) -> bool:
    for evidence_id in evidence_ids:
        item = evidence_by_id.get(evidence_id) or {}
        if (item.get("pdf_context_flags") or {}).get("has_images") is True:
            return True
    return False


def build_claim_tasks(draft: dict[str, Any], context: dict[str, Any]) -> list[ReviewClaimTask]:
    evidence_by_id = evidence_lookup(context)
    tasks: list[ReviewClaimTask] = []
    for section in draft.get("sections", []):
        section_id = section.get("section_id") or "UNKNOWN_SECTION"
        for claim in section.get("claims", []):
            evidence_ids = list(claim.get("evidence_ids") or [])
            claim_type = claim.get("claim_type") or "UNKNOWN_CLAIM_TYPE"
            requires_evidence_review = bool(evidence_ids)
            requires_visual_review = claim_requires_visual_review(evidence_ids, evidence_by_id)
            tasks.append(
                ReviewClaimTask(
                    claim_id=claim.get("claim_id") or "UNKNOWN_CLAIM",
                    section_id=section_id,
                    claim_type=claim_type,
                    review_status="PENDING_REVIEW",
                    evidence_ids=evidence_ids,
                    requires_evidence_review=requires_evidence_review,
                    requires_visual_review=requires_visual_review,
                    reviewer_decision="UNSET",
                    reviewer_notes="",
                )
            )
    return tasks


def build_gap_tasks(draft: dict[str, Any]) -> list[ReviewGapTask]:
    tasks: list[ReviewGapTask] = []
    index = 1
    for section in draft.get("sections", []):
        for gap in section.get("unresolved_gaps", []) or []:
            tasks.append(
                ReviewGapTask(
                    gap_id=f"gap_{index:03d}",
                    review_status="PENDING_ACKNOWLEDGEMENT",
                    gap_text=gap,
                    acknowledgement_status="UNSET",
                    reviewer_notes="",
                )
            )
            index += 1
    return tasks


def build_manifest(draft_path: Path, context_path: Path) -> KBDraftReviewManifest:
    root = repo_root()
    draft = read_json(draft_path)
    context = read_json(context_path)
    claim_tasks = build_claim_tasks(draft, context)
    gap_tasks = build_gap_tasks(draft)
    visual_task_count = sum(1 for task in claim_tasks if task.requires_visual_review)
    evidence_task_count = sum(1 for task in claim_tasks if task.requires_evidence_review)

    return KBDraftReviewManifest(
        artifact_type="kb_draft_review_manifest",
        schema_version="kb_draft_review_manifest.v1",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        review_status="PENDING_REVIEW",
        source_draft_path=relpath(draft_path, root),
        source_context_path=relpath(context_path, root),
        review_policy={
            "claims_default_to_pending": True,
            "accepted_claims_require_evidence_ids": True,
            "image_bearing_claims_require_visual_acknowledgement": True,
            "unresolved_gaps_require_acknowledgement": True,
            "finalization_allowed": False,
            "reviewer_decisions_allowed": ["UNSET", "ACCEPT", "REJECT", "NEEDS_MORE_EVIDENCE"],
        },
        diagnostics={
            "claim_review_tasks": len(claim_tasks),
            "evidence_review_tasks": evidence_task_count,
            "visual_review_tasks": visual_task_count,
            "unresolved_gap_tasks": len(gap_tasks),
            "accepted_claims": 0,
            "rejected_claims": 0,
            "needs_more_evidence_claims": 0,
            "acknowledged_gaps": 0,
        },
        claim_review_tasks=claim_tasks,
        unresolved_gap_tasks=gap_tasks,
    )


def write_manifest(manifest: KBDraftReviewManifest, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build Gate 9 draft review manifest from constrained impact draft.")
    parser.add_argument("--draft", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_draft.v1.json")
    parser.add_argument("--context", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_context.v2.enriched.json")
    parser.add_argument("--output", type=Path, default=root / "kbs" / "review" / "kb_draft_review_manifest.v1.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_manifest(args.draft, args.context)
    write_manifest(manifest, args.output)
    print(f"Wrote KB draft review manifest: {args.output}")
    print(f"Review status: {manifest.review_status}")
    print(f"Claim review tasks: {manifest.diagnostics['claim_review_tasks']}")
    print(f"Visual review tasks: {manifest.diagnostics['visual_review_tasks']}")
    print(f"Unresolved gap tasks: {manifest.diagnostics['unresolved_gap_tasks']}")


if __name__ == "__main__":
    main()
