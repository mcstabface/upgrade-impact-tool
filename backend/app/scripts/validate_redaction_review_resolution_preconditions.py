from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.redaction_review_resolution_preconditions import (
    DEFAULT_RESPONSE_JSONL,
    DEFAULT_REVIEW_EXPORT_JSON,
    DEFAULT_VECTOR_INDEX_PATH,
    DEFAULT_VECTOR_PATH,
    build_submission_precondition_report,
    write_json,
    write_resolution_fixture,
    write_submission_precondition_report,
)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def assert_all_allowed_fixture_reaches_dry_run_ready() -> None:
    root = repo_root()
    review_export = root / DEFAULT_REVIEW_EXPORT_JSON
    if not review_export.exists():
        raise AssertionError(f"Expected Gate 18J review export: {review_export}")
    with tempfile.TemporaryDirectory() as temp_dir:
        fixture_path = Path(temp_dir) / "resolution_fixture.json"
        precondition_path = Path(temp_dir) / "preconditions.json"
        fixture = write_resolution_fixture(review_export_path=review_export, output_path=fixture_path)
        items = fixture.get("items")
        if not isinstance(items, list) or not items:
            raise AssertionError("Resolution fixture must preserve review items")
        for item in items:
            if not isinstance(item, dict):
                raise AssertionError("Resolution fixture item must be object")
            if item.get("reviewer_decision") != "ALLOW_TECHNICAL_IDENTIFIER":
                raise AssertionError(f"Expected all-allowed fixture decision, got: {item}")
            if not str(item.get("reviewer_notes") or "").strip():
                raise AssertionError("Fixture terminal decisions require notes")
        report = build_submission_precondition_report(review_export_path=review_export, fixture_path=fixture_path)
        if report.status != "PRECONDITIONS_READY_DRY_RUN_ONLY":
            raise AssertionError(f"Expected ready dry-run status, got: {report.status}")
        if report.failed_count != 0:
            raise AssertionError(f"Expected zero failed checks, got: {report.failed_count}")
        if report.real_submission_allowed is not False:
            raise AssertionError("Precondition report must not allow real submission")
        if report.dry_run_only is not True:
            raise AssertionError("Precondition report must remain dry-run only")
        if report.vectors_created is not False:
            raise AssertionError("Precondition report must not create vectors")
        write_submission_precondition_report(precondition_path, report)
        persisted = read_json(precondition_path)
        if persisted.get("real_submission_allowed") is not False:
            raise AssertionError("Persisted precondition report must forbid real submission")


def assert_blocked_fixture_fails_preconditions() -> None:
    root = repo_root()
    review_export = root / DEFAULT_REVIEW_EXPORT_JSON
    source = read_json(review_export)
    clone = copy.deepcopy(source)
    items = clone.get("items")
    if not isinstance(items, list) or not items:
        raise AssertionError("Expected review items for blocked fixture")
    first = items[0]
    if not isinstance(first, dict):
        raise AssertionError("Review item must be object")
    first["reviewer_decision"] = "BLOCK_EMBEDDING"
    first["reviewer_notes"] = "Blocked fixture."
    first["reviewer"] = "gate18m-validator"
    for item in items[1:]:
        if isinstance(item, dict):
            item["reviewer_decision"] = "ALLOW_TECHNICAL_IDENTIFIER"
            item["reviewer_notes"] = "Allowed fixture."
            item["reviewer"] = "gate18m-validator"
    clone["embedding_submission_allowed"] = False
    clone["vectors_created"] = False

    with tempfile.TemporaryDirectory() as temp_dir:
        fixture_path = Path(temp_dir) / "blocked_fixture.json"
        write_json(fixture_path, clone)
        report = build_submission_precondition_report(review_export_path=review_export, fixture_path=fixture_path)
        if report.status != "PRECONDITIONS_BLOCKED":
            raise AssertionError(f"Expected blocked precondition status, got: {report.status}")
        if report.failed_count < 1:
            raise AssertionError("Expected at least one failed check")
        if "no_block_embedding_decisions" not in report.blockers:
            raise AssertionError(f"Expected block decision precondition failure, got: {report.blockers}")
        if report.real_submission_allowed is not False:
            raise AssertionError("Blocked report must not allow real submission")


def assert_submission_allowed_fixture_is_rejected() -> None:
    root = repo_root()
    review_export = root / DEFAULT_REVIEW_EXPORT_JSON
    source = read_json(review_export)
    clone = copy.deepcopy(source)
    clone["embedding_submission_allowed"] = True
    clone["vectors_created"] = False
    with tempfile.TemporaryDirectory() as temp_dir:
        fixture_path = Path(temp_dir) / "bad_fixture.json"
        write_json(fixture_path, clone)
        try:
            build_submission_precondition_report(review_export_path=review_export, fixture_path=fixture_path)
        except ValueError as exc:
            if "embedding_submission_allowed false" not in str(exc):
                raise AssertionError(f"Unexpected rejection reason: {exc}") from exc
        else:
            raise AssertionError("Expected fixture with embedding_submission_allowed=true to be rejected")


def assert_no_response_or_vector_outputs_exist() -> None:
    root = repo_root()
    for relative in (DEFAULT_RESPONSE_JSONL, DEFAULT_VECTOR_PATH, DEFAULT_VECTOR_INDEX_PATH):
        if (root / relative).exists():
            raise AssertionError(f"Gate 18M must not create response/vector artifact: {relative}")


def main() -> None:
    assert_all_allowed_fixture_reaches_dry_run_ready()
    assert_blocked_fixture_fails_preconditions()
    assert_submission_allowed_fixture_is_rejected()
    assert_no_response_or_vector_outputs_exist()
    print("[gate18m:preconditions] OK")
    print("[gate18m:preconditions] all_allowed_fixture=ready_dry_run_only")
    print("[gate18m:preconditions] blockers=enforced")
    print("[gate18m:preconditions] submission_preconditions=validated")
    print("[gate18m:preconditions] real_submission_allowed=false")
    print("[gate18m:preconditions] vectors=not_created")


if __name__ == "__main__":
    main()
