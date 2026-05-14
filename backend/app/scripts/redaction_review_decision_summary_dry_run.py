from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.update_redaction_review_decisions import ALLOWED_DECISIONS


DEFAULT_REVIEW_EXPORT_JSON = "kbs/retrieval/kb_embedding_unresolved_redaction_review.v1.json"
DEFAULT_DECISION_SUMMARY_REPORT = "kbs/retrieval/kb_embedding_redaction_review_decision_summary.v1.json"
DEFAULT_RESPONSE_JSONL = "kbs/retrieval/kb_embedding_batch_responses.v1.jsonl"
DEFAULT_VECTOR_PATH = "kbs/retrieval/kb_vectors.v1.jsonl"
DEFAULT_VECTOR_INDEX_PATH = "kbs/retrieval/kb_vector_index.v1.json"


@dataclass(frozen=True)
class RedactionDecisionSummaryCounts:
    item_count: int
    pending_count: int
    allow_technical_identifier_count: int
    mask_before_embedding_count: int
    block_embedding_count: int
    unsupported_decision_count: int
    effective_blocking_count: int


@dataclass(frozen=True)
class RedactionDecisionSummaryReport:
    report_version: str
    status: str
    source_review_export: str
    counts: RedactionDecisionSummaryCounts
    blocking_review_ids: list[str] = field(default_factory=list)
    allowed_review_ids: list[str] = field(default_factory=list)
    mask_required_review_ids: list[str] = field(default_factory=list)
    block_embedding_review_ids: list[str] = field(default_factory=list)
    embedding_submission_allowed: bool = False
    dry_run_only: bool = True
    vectors_created: bool = False


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def build_decision_summary_report(*, review_export_path: Path) -> RedactionDecisionSummaryReport:
    if not review_export_path.exists():
        raise FileNotFoundError(f"Review export not found: {review_export_path}")
    review_export = read_json(review_export_path)
    if review_export.get("embedding_submission_allowed") is not False:
        raise ValueError("Review export must keep embedding_submission_allowed false")
    if review_export.get("vectors_created") is not False:
        raise ValueError("Review export must keep vectors_created false")
    items = review_export.get("items")
    if not isinstance(items, list):
        raise ValueError("Review export items must be a list")

    pending: list[str] = []
    allowed: list[str] = []
    mask_required: list[str] = []
    block_embedding: list[str] = []
    unsupported: list[str] = []

    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Review export item must be an object")
        review_id = str(item.get("review_id") or "")
        if not review_id:
            raise ValueError("Review export item missing review_id")
        decision = str(item.get("reviewer_decision") or "PENDING")
        if decision not in ALLOWED_DECISIONS:
            unsupported.append(review_id)
        elif decision == "PENDING":
            pending.append(review_id)
        elif decision == "ALLOW_TECHNICAL_IDENTIFIER":
            allowed.append(review_id)
        elif decision == "MASK_BEFORE_EMBEDDING":
            mask_required.append(review_id)
        elif decision == "BLOCK_EMBEDDING":
            block_embedding.append(review_id)

    blocking_review_ids = sorted(pending + mask_required + block_embedding + unsupported)
    effective_blocking_count = len(blocking_review_ids)
    if unsupported:
        status = "SUMMARY_INVALID_UNSUPPORTED_DECISIONS"
    elif effective_blocking_count:
        status = "SUMMARY_BLOCKED"
    else:
        status = "SUMMARY_NO_REVIEW_BLOCKERS_DRY_RUN_ONLY"

    root = repo_root()
    source_review_export = str(review_export_path.relative_to(root)) if review_export_path.is_relative_to(root) else str(review_export_path)
    return RedactionDecisionSummaryReport(
        report_version="1",
        status=status,
        source_review_export=source_review_export,
        counts=RedactionDecisionSummaryCounts(
            item_count=len(items),
            pending_count=len(pending),
            allow_technical_identifier_count=len(allowed),
            mask_before_embedding_count=len(mask_required),
            block_embedding_count=len(block_embedding),
            unsupported_decision_count=len(unsupported),
            effective_blocking_count=effective_blocking_count,
        ),
        blocking_review_ids=blocking_review_ids,
        allowed_review_ids=sorted(allowed),
        mask_required_review_ids=sorted(mask_required),
        block_embedding_review_ids=sorted(block_embedding),
        embedding_submission_allowed=False,
        dry_run_only=True,
        vectors_created=False,
    )


def write_decision_summary_report(path: Path, report: RedactionDecisionSummaryReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build Gate 18L redaction review decision summary dry-run report.")
    parser.add_argument("--review-export", type=Path, default=root / DEFAULT_REVIEW_EXPORT_JSON)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_DECISION_SUMMARY_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_decision_summary_report(review_export_path=args.review_export)
    write_decision_summary_report(args.output, report)
    print(f"[gate18l:summary] Wrote decision summary report: {args.output}")
    print(f"[gate18l:summary] status={report.status}")
    print(f"[gate18l:summary] item_count={report.counts.item_count}")
    print(f"[gate18l:summary] pending_count={report.counts.pending_count}")
    print(f"[gate18l:summary] effective_blocking_count={report.counts.effective_blocking_count}")
    print("[gate18l:summary] embedding_submission=forbidden")
    print("[gate18l:summary] vectors=not_created")


if __name__ == "__main__":
    main()
