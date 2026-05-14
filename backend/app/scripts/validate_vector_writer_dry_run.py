from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.vector_writer_dry_run_validator import (
    DEFAULT_RESPONSE_FIXTURE_JSONL,
    DEFAULT_VECTOR_INDEX_PATH,
    DEFAULT_VECTOR_PATH,
    build_vector_writer_dry_run_report,
    read_jsonl,
    write_vector_writer_dry_run_report,
)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def assert_valid_fixture_produces_candidate_vectors() -> None:
    response_fixture = repo_root() / DEFAULT_RESPONSE_FIXTURE_JSONL
    if not response_fixture.exists():
        raise AssertionError(f"Expected Gate 18O response fixture: {response_fixture}")
    report = build_vector_writer_dry_run_report(response_fixture_path=response_fixture)
    if report.status != "DRY_RUN_VALID":
        raise AssertionError(f"Expected valid dry-run report, got: {report.status} {report.validation_errors}")
    if report.candidate_vector_count != 3:
        raise AssertionError(f"Expected 3 candidate vectors, got: {report.candidate_vector_count}")
    if report.validation_error_count != 0:
        raise AssertionError(f"Expected zero validation errors, got: {report.validation_errors}")
    if report.vector_outputs_created is not False:
        raise AssertionError("Dry-run report must not create vector outputs")
    if report.dry_run_only is not True:
        raise AssertionError("Dry-run report must remain dry-run only")
    vector_ids = [record.vector_record_id for record in report.candidate_vectors]
    if len(vector_ids) != len(set(vector_ids)):
        raise AssertionError("Candidate vector IDs must be unique")
    for vector_id in vector_ids:
        if not vector_id.startswith("vec_"):
            raise AssertionError(f"Unexpected vector ID: {vector_id}")

    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "dry_run_report.json"
        write_vector_writer_dry_run_report(output, report)
        persisted = read_json(output)
        if persisted.get("vector_outputs_created") is not False:
            raise AssertionError("Persisted report must not create vector outputs")


def assert_invalid_dimension_fixture_fails_without_candidates() -> None:
    source_rows = read_jsonl(repo_root() / DEFAULT_RESPONSE_FIXTURE_JSONL)
    rows = copy.deepcopy(source_rows)
    rows[0]["embedding_vector"] = rows[0]["embedding_vector"][:-1]
    with tempfile.TemporaryDirectory() as temp_dir:
        fixture = Path(temp_dir) / "bad_dimensions.jsonl"
        write_jsonl(fixture, rows)
        report = build_vector_writer_dry_run_report(response_fixture_path=fixture)
        if report.status != "DRY_RUN_INVALID":
            raise AssertionError(f"Expected invalid dry-run report, got: {report.status}")
        if report.validation_error_count < 1:
            raise AssertionError("Expected at least one validation error")
        if report.candidate_vectors:
            raise AssertionError("Invalid dry-run report must not expose candidate vectors")


def assert_duplicate_cache_key_fixture_fails_without_candidates() -> None:
    source_rows = read_jsonl(repo_root() / DEFAULT_RESPONSE_FIXTURE_JSONL)
    rows = copy.deepcopy(source_rows)
    rows[1]["embedding_cache_key"] = rows[0]["embedding_cache_key"]
    with tempfile.TemporaryDirectory() as temp_dir:
        fixture = Path(temp_dir) / "duplicate_cache_key.jsonl"
        write_jsonl(fixture, rows)
        report = build_vector_writer_dry_run_report(response_fixture_path=fixture)
        if report.status != "DRY_RUN_INVALID":
            raise AssertionError(f"Expected invalid dry-run report, got: {report.status}")
        if not any("duplicate embedding_cache_key" in error for error in report.validation_errors):
            raise AssertionError(f"Expected duplicate cache key error, got: {report.validation_errors}")
        if report.candidate_vectors:
            raise AssertionError("Duplicate dry-run report must not expose candidate vectors")


def assert_no_vector_outputs_exist() -> None:
    root = repo_root()
    for relative in (DEFAULT_VECTOR_PATH, DEFAULT_VECTOR_INDEX_PATH):
        if (root / relative).exists():
            raise AssertionError(f"Gate 18P must not create vector artifact: {relative}")


def main() -> None:
    assert_valid_fixture_produces_candidate_vectors()
    assert_invalid_dimension_fixture_fails_without_candidates()
    assert_duplicate_cache_key_fixture_fails_without_candidates()
    assert_no_vector_outputs_exist()
    print("[gate18p:vector-dry-run] OK")
    print("[gate18p:vector-dry-run] valid_fixture=candidate_vectors")
    print("[gate18p:vector-dry-run] invalid_dimensions=fail_closed")
    print("[gate18p:vector-dry-run] duplicate_cache_key=fail_closed")
    print("[gate18p:vector-dry-run] vectors=not_created")


if __name__ == "__main__":
    main()
