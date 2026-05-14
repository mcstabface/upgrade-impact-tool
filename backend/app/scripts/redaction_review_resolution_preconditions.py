from __future__ import annotations

import argparse
import copy
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.redaction_review_decision_summary_dry_run import build_decision_summary_report


DEFAULT_REVIEW_EXPORT_JSON = "kbs/retrieval/kb_embedding_unresolved_redaction_review.v1.json"
DEFAULT_RESOLUTION_FIXTURE = "kbs/retrieval/kb_embedding_redaction_review_resolution_fixture.v1.json"
DEFAULT_PRECONDITION_REPORT = "kbs/retrieval/kb_embedding_submission_preconditions.v1.json"
DEFAULT_RESPONSE_JSONL = "kbs/retrieval/kb_embedding_batch_responses.v1.jsonl"
DEFAULT_VECTOR_PATH = "kbs/retrieval/kb_vectors.v1.jsonl"
DEFAULT_VECTOR_INDEX_PATH = "kbs/retrieval/kb_vector_index.v1.json"


@dataclass(frozen=True)
class SubmissionPreconditionCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class SubmissionPreconditionReport:
    report_version: str
    status: str
    source_review_export: str
    fixture_path: str
    checks: list[SubmissionPreconditionCheck]
    passed_count: int
    failed_count: int
    real_submission_allowed: bool = False
    dry_run_only: bool = True
    vectors_created: bool = False
    blockers: list[str] = field(default_factory=list)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def build_all_allowed_resolution_fixture(*, review_export_path: Path) -> dict[str, Any]:
    if not review_export_path.exists():
        raise FileNotFoundError(f"Review export not found: {review_export_path}")
    fixture = copy.deepcopy(read_json(review_export_path))
    items = fixture.get("items")
    if not isinstance(items, list):
        raise ValueError("Review export items must be a list")
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Review export item must be an object")
        item["reviewer_decision"] = "ALLOW_TECHNICAL_IDENTIFIER"
        item["reviewer_notes"] = "Gate 18M deterministic fixture: reviewed as technical identifier."
        item["reviewer"] = "gate18m-fixture"
    fixture["status"] = "REVIEW_COMPLETE_FIXTURE"
    fixture["embedding_submission_allowed"] = False
    fixture["vectors_created"] = False
    fixture["decision_summary"] = {
        "pending_count": 0,
        "terminal_decision_count": len(items),
        "allow_technical_identifier_count": len(items),
        "mask_before_embedding_count": 0,
        "block_embedding_count": 0,
    }
    return fixture


def write_resolution_fixture(*, review_export_path: Path, output_path: Path) -> dict[str, Any]:
    fixture = build_all_allowed_resolution_fixture(review_export_path=review_export_path)
    write_json(output_path, fixture)
    return fixture


def build_submission_precondition_report(*, review_export_path: Path, fixture_path: Path) -> SubmissionPreconditionReport:
    if not fixture_path.exists():
        raise FileNotFoundError(f"Resolution fixture not found: {fixture_path}")
    fixture = read_json(fixture_path)
    summary = build_decision_summary_report(review_export_path=fixture_path)
    checks: list[SubmissionPreconditionCheck] = []
    blockers: list[str] = []

    def add_check(name: str, passed: bool, detail: str) -> None:
        checks.append(SubmissionPreconditionCheck(name=name, passed=passed, detail=detail))
        if not passed:
            blockers.append(name)

    items = fixture.get("items")
    add_check("review_items_present", isinstance(items, list) and len(items) > 0, "Review fixture must contain review items.")
    add_check("no_pending_decisions", summary.counts.pending_count == 0, f"pending_count={summary.counts.pending_count}")
    add_check("no_mask_required_decisions", summary.counts.mask_before_embedding_count == 0, f"mask_before_embedding_count={summary.counts.mask_before_embedding_count}")
    add_check("no_block_embedding_decisions", summary.counts.block_embedding_count == 0, f"block_embedding_count={summary.counts.block_embedding_count}")
    add_check("no_unsupported_decisions", summary.counts.unsupported_decision_count == 0, f"unsupported_decision_count={summary.counts.unsupported_decision_count}")
    add_check("no_effective_blockers", summary.counts.effective_blocking_count == 0, f"effective_blocking_count={summary.counts.effective_blocking_count}")
    add_check("summary_dry_run_only", summary.dry_run_only is True, "Decision summary must remain dry-run only.")
    add_check("summary_submission_forbidden", summary.embedding_submission_allowed is False, "Decision summary must forbid embedding submission.")
    add_check("fixture_submission_forbidden", fixture.get("embedding_submission_allowed") is False, "Fixture must forbid embedding submission.")
    add_check("fixture_vectors_not_created", fixture.get("vectors_created") is False, "Fixture must not create vectors.")

    failed_count = sum(1 for check in checks if not check.passed)
    passed_count = len(checks) - failed_count
    root = repo_root()
    source_review_export = str(review_export_path.relative_to(root)) if review_export_path.is_relative_to(root) else str(review_export_path)
    fixture_relative = str(fixture_path.relative_to(root)) if fixture_path.is_relative_to(root) else str(fixture_path)
    return SubmissionPreconditionReport(
        report_version="1",
        status="PRECONDITIONS_READY_DRY_RUN_ONLY" if failed_count == 0 else "PRECONDITIONS_BLOCKED",
        source_review_export=source_review_export,
        fixture_path=fixture_relative,
        checks=checks,
        passed_count=passed_count,
        failed_count=failed_count,
        real_submission_allowed=False,
        dry_run_only=True,
        vectors_created=False,
        blockers=blockers,
    )


def write_submission_precondition_report(path: Path, report: SubmissionPreconditionReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build Gate 18M review resolution fixture and submission precondition report.")
    parser.add_argument("--review-export", type=Path, default=root / DEFAULT_REVIEW_EXPORT_JSON)
    parser.add_argument("--fixture-output", type=Path, default=root / DEFAULT_RESOLUTION_FIXTURE)
    parser.add_argument("--precondition-output", type=Path, default=root / DEFAULT_PRECONDITION_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    write_resolution_fixture(review_export_path=args.review_export, output_path=args.fixture_output)
    report = build_submission_precondition_report(review_export_path=args.review_export, fixture_path=args.fixture_output)
    write_submission_precondition_report(args.precondition_output, report)
    print(f"[gate18m:preconditions] Wrote resolution fixture: {args.fixture_output}")
    print(f"[gate18m:preconditions] Wrote precondition report: {args.precondition_output}")
    print(f"[gate18m:preconditions] status={report.status}")
    print(f"[gate18m:preconditions] passed_checks={report.passed_count}")
    print(f"[gate18m:preconditions] failed_checks={report.failed_count}")
    print("[gate18m:preconditions] real_submission_allowed=false")
    print("[gate18m:preconditions] vectors=not_created")


if __name__ == "__main__":
    main()
