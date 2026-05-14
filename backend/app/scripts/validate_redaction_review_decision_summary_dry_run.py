from __future__ import annotations

import argparse
import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.redaction_review_decision_summary_dry_run import (
    DEFAULT_RESPONSE_JSONL,
    DEFAULT_REVIEW_EXPORT_JSON,
    DEFAULT_VECTOR_INDEX_PATH,
    DEFAULT_VECTOR_PATH,
    build_decision_summary_report,
    write_decision_summary_report,
)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_current_review_summary_builds() -> None:
    root = repo_root()
    review_export = root / DEFAULT_REVIEW_EXPORT_JSON
    if not review_export.exists():
        raise AssertionError(f"Expected Gate 18J review export: {review_export}")
    source = read_json(review_export)
    items = source.get("items")
    if not isinstance(items, list):
        raise AssertionError("Review export items must be list")

    report = build_decision_summary_report(review_export_path=review_export)
    if report.counts.item_count != len(items):
        raise AssertionError("Summary item count mismatch")
    if report.embedding_submission_allowed is not False:
        raise AssertionError("Summary must not allow embedding submission")
    if report.dry_run_only is not True:
        raise AssertionError("Summary must remain dry-run only")
    if report.vectors_created is not False:
        raise AssertionError("Summary must not create vectors")
    if report.counts.pending_count:
        if report.status != "SUMMARY_BLOCKED":
            raise AssertionError(f"Expected SUMMARY_BLOCKED with pending decisions, got: {report.status}")
        if report.counts.effective_blocking_count < report.counts.pending_count:
            raise AssertionError("Effective blockers must include pending decisions")

    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "summary.json"
        write_decision_summary_report(output, report)
        persisted = read_json(output)
        if persisted.get("embedding_submission_allowed") is not False:
            raise AssertionError("Persisted summary must forbid embedding submission")
        counts = persisted.get("counts")
        if not isinstance(counts, dict):
            raise AssertionError("Persisted summary missing counts")
        if counts.get("item_count") != len(items):
            raise AssertionError("Persisted summary item count mismatch")


def assert_all_allowed_is_still_dry_run_only() -> None:
    root = repo_root()
    source = read_json(root / DEFAULT_REVIEW_EXPORT_JSON)
    clone = copy.deepcopy(source)
    items = clone.get("items")
    if not isinstance(items, list) or not items:
        raise AssertionError("Expected review items for all-allowed fixture")
    for item in items:
        if not isinstance(item, dict):
            raise AssertionError("Review item must be object")
        item["reviewer_decision"] = "ALLOW_TECHNICAL_IDENTIFIER"
        item["reviewer_notes"] = "Validated as technical identifier fixture."
        item["reviewer"] = "gate18l-validator"

    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "all_allowed_review.json"
        write_json(path, clone)
        report = build_decision_summary_report(review_export_path=path)
        if report.status != "SUMMARY_NO_REVIEW_BLOCKERS_DRY_RUN_ONLY":
            raise AssertionError(f"Expected no-blockers dry-run status, got: {report.status}")
        if report.counts.effective_blocking_count != 0:
            raise AssertionError("All-allowed fixture should have zero effective blockers")
        if report.embedding_submission_allowed is not False:
            raise AssertionError("All-allowed fixture must still forbid embedding submission")
        if report.dry_run_only is not True:
            raise AssertionError("All-allowed fixture must remain dry-run only")


def assert_mask_and_block_decisions_remain_blocking() -> None:
    root = repo_root()
    source = read_json(root / DEFAULT_REVIEW_EXPORT_JSON)
    clone = copy.deepcopy(source)
    items = clone.get("items")
    if not isinstance(items, list) or len(items) < 2:
        raise AssertionError("Expected at least two review items")
    assert isinstance(items[0], dict)
    assert isinstance(items[1], dict)
    items[0]["reviewer_decision"] = "MASK_BEFORE_EMBEDDING"
    items[0]["reviewer_notes"] = "Must be masked first."
    items[0]["reviewer"] = "gate18l-validator"
    items[1]["reviewer_decision"] = "BLOCK_EMBEDDING"
    items[1]["reviewer_notes"] = "Must block embedding."
    items[1]["reviewer"] = "gate18l-validator"
    for item in items[2:]:
        if isinstance(item, dict):
            item["reviewer_decision"] = "ALLOW_TECHNICAL_IDENTIFIER"
            item["reviewer_notes"] = "Validated as technical identifier fixture."
            item["reviewer"] = "gate18l-validator"

    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "blocked_review.json"
        write_json(path, clone)
        report = build_decision_summary_report(review_export_path=path)
        if report.status != "SUMMARY_BLOCKED":
            raise AssertionError(f"Expected blocked status, got: {report.status}")
        if report.counts.mask_before_embedding_count != 1:
            raise AssertionError("Expected one mask-required decision")
        if report.counts.block_embedding_count != 1:
            raise AssertionError("Expected one block decision")
        if report.counts.effective_blocking_count != 2:
            raise AssertionError(f"Expected exactly two blockers, got: {report.counts.effective_blocking_count}")


def assert_no_response_or_vector_outputs_exist() -> None:
    root = repo_root()
    for relative in (DEFAULT_RESPONSE_JSONL, DEFAULT_VECTOR_PATH, DEFAULT_VECTOR_INDEX_PATH):
        if (root / relative).exists():
            raise AssertionError(f"Gate 18L must not create response/vector artifact: {relative}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 18L redaction review decision summary dry run.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_current_review_summary_builds()
    assert_all_allowed_is_still_dry_run_only()
    assert_mask_and_block_decisions_remain_blocking()
    assert_no_response_or_vector_outputs_exist()
    print("[gate18l:summary] OK")
    print("[gate18l:summary] decision_counts=valid")
    print("[gate18l:summary] blockers=enforced")
    print("[gate18l:summary] all_allowed=dry_run_only")
    print("[gate18l:summary] embedding_submission=forbidden")
    print("[gate18l:summary] vectors=not_created")


if __name__ == "__main__":
    main()
