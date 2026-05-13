from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.embedding_dry_run_submission_contract import (
    DEFAULT_DRY_RUN_SUBMISSION_REPORT,
    DEFAULT_FULL_TEXT_PAYLOAD_REPORT,
    DEFAULT_FULL_TEXT_REQUEST_JSONL,
    DEFAULT_RESPONSE_JSONL,
    DEFAULT_VECTOR_INDEX_PATH,
    DEFAULT_VECTOR_PATH,
    build_dry_run_submission_decision,
    build_dry_run_submission_report,
    write_dry_run_submission_report,
)
from app.scripts.extract_kb_source_manifest import repo_root


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def assert_decision_states() -> None:
    no_requests = build_dry_run_submission_decision(request_count=0, finding_count=0)
    if no_requests.status != "REFUSED" or no_requests.reason != "NO_REQUESTS":
        raise AssertionError(f"Expected NO_REQUESTS refusal, got: {no_requests}")

    redaction_blocked = build_dry_run_submission_decision(request_count=10, finding_count=1)
    if redaction_blocked.status != "REFUSED" or redaction_blocked.reason != "REDACTION_FINDINGS_PRESENT":
        raise AssertionError(f"Expected redaction refusal, got: {redaction_blocked}")
    if redaction_blocked.real_submission_allowed is not False:
        raise AssertionError("Redaction-blocked decision must not allow real submission.")

    ready = build_dry_run_submission_decision(request_count=10, finding_count=0)
    if ready.status != "DRY_RUN_READY":
        raise AssertionError(f"Expected dry-run ready, got: {ready}")
    if ready.would_submit is not True:
        raise AssertionError("Dry-run ready decision should indicate would_submit true.")
    if ready.real_submission_allowed is not False:
        raise AssertionError("Dry-run ready decision must still forbid real submission.")


def assert_report_builds_from_gate18f_outputs() -> None:
    root = repo_root()
    request_jsonl = root / DEFAULT_FULL_TEXT_REQUEST_JSONL
    payload_report = root / DEFAULT_FULL_TEXT_PAYLOAD_REPORT
    if not request_jsonl.exists():
        raise AssertionError(f"Expected Gate 18F full-text request JSONL: {request_jsonl}")
    if not payload_report.exists():
        raise AssertionError(f"Expected Gate 18F payload report: {payload_report}")

    report = build_dry_run_submission_report(request_jsonl_path=request_jsonl, payload_report_path=payload_report)
    if report.request_count <= 0:
        raise AssertionError(f"Expected positive request count, got: {report.request_count}")
    if report.finding_count > 0:
        if report.status != "REFUSED":
            raise AssertionError(f"Expected REFUSED when findings exist, got: {report.status}")
        if report.decision.reason != "REDACTION_FINDINGS_PRESENT":
            raise AssertionError(f"Expected redaction refusal reason, got: {report.decision}")
    else:
        if report.status != "DRY_RUN_READY":
            raise AssertionError(f"Expected DRY_RUN_READY with no findings, got: {report.status}")
    if report.dry_run_only is not True:
        raise AssertionError("Dry-run report must mark dry_run_only true.")
    if report.real_submission_allowed is not False:
        raise AssertionError("Dry-run report must forbid real submission.")
    if report.vectors_created is not False:
        raise AssertionError("Dry-run report must not create vectors.")
    schema = report.simulated_response_schema
    if schema.get("response_jsonl_path") != DEFAULT_RESPONSE_JSONL:
        raise AssertionError(f"Unexpected simulated response path: {schema}")
    vector_outputs = schema.get("vector_store_outputs")
    if not isinstance(vector_outputs, dict):
        raise AssertionError(f"Expected vector_store_outputs schema: {schema}")
    if vector_outputs.get("vector_jsonl_path") != DEFAULT_VECTOR_PATH:
        raise AssertionError(f"Unexpected vector path schema: {schema}")
    if vector_outputs.get("vector_index_path") != DEFAULT_VECTOR_INDEX_PATH:
        raise AssertionError(f"Unexpected vector index path schema: {schema}")

    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "dry_run_report.json"
        write_dry_run_submission_report(output, report)
        persisted = read_json(output)
        if persisted.get("request_count") != report.request_count:
            raise AssertionError("Persisted dry-run report request count mismatch")
        if persisted.get("real_submission_allowed") is not False:
            raise AssertionError("Persisted dry-run report must forbid real submission")


def assert_no_response_or_vector_outputs_exist() -> None:
    root = repo_root()
    for relative in (DEFAULT_RESPONSE_JSONL, DEFAULT_VECTOR_PATH, DEFAULT_VECTOR_INDEX_PATH):
        if (root / relative).exists():
            raise AssertionError(f"Gate 18G must not create response/vector artifact: {relative}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 18G dry-run embedding submission contract.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_decision_states()
    assert_report_builds_from_gate18f_outputs()
    assert_no_response_or_vector_outputs_exist()
    print("[gate18g:dry-run] OK")
    print("[gate18g:dry-run] contract=valid")
    print("[gate18g:dry-run] redaction_findings=refuse_submission")
    print("[gate18g:dry-run] real_submission_allowed=false")
    print("[gate18g:dry-run] simulated_response_schema=valid")
    print("[gate18g:dry-run] vectors=not_created")


if __name__ == "__main__":
    main()
