from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.embedding_submission_adapter import (
    DEFAULT_FULL_TEXT_REQUEST_JSONL,
    DEFAULT_PRECONDITION_REPORT,
    DEFAULT_RESPONSE_JSONL,
    DEFAULT_VECTOR_INDEX_PATH,
    DEFAULT_VECTOR_PATH,
    build_submission_adapter_report,
    get_embedding_submission_adapter,
    read_json,
    write_submission_adapter_report,
)
from app.scripts.extract_kb_source_manifest import repo_root


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_disabled_adapter_refuses_ready_preconditions() -> None:
    root = repo_root()
    request_jsonl = root / DEFAULT_FULL_TEXT_REQUEST_JSONL
    preconditions = root / DEFAULT_PRECONDITION_REPORT
    if not request_jsonl.exists():
        raise AssertionError(f"Expected full-text request JSONL: {request_jsonl}")
    if not preconditions.exists():
        raise AssertionError(f"Expected Gate 18M precondition report: {preconditions}")
    result = build_submission_adapter_report(
        request_jsonl_path=request_jsonl,
        precondition_report_path=preconditions,
        adapter_name="disabled",
    )
    if result.status != "REFUSED":
        raise AssertionError(f"Disabled adapter must refuse, got: {result.status}")
    if result.reason != "DISABLED_ADAPTER_REFUSES_REAL_SUBMISSION":
        raise AssertionError(f"Expected disabled refusal reason, got: {result.reason}")
    if result.request_count <= 0:
        raise AssertionError(f"Expected positive request count, got: {result.request_count}")
    if result.errors:
        raise AssertionError(f"Expected no input errors for ready preconditions, got: {result.errors}")
    if result.real_submission_allowed is not False:
        raise AssertionError("Disabled adapter must keep real submission forbidden")
    if result.would_submit is not False:
        raise AssertionError("Disabled adapter must not indicate would_submit")
    if result.response_jsonl_path != DEFAULT_RESPONSE_JSONL:
        raise AssertionError("Unexpected response JSONL path")
    if result.vector_jsonl_path != DEFAULT_VECTOR_PATH:
        raise AssertionError("Unexpected vector JSONL path")
    if result.vector_index_path != DEFAULT_VECTOR_INDEX_PATH:
        raise AssertionError("Unexpected vector index path")

    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "adapter_report.json"
        write_submission_adapter_report(output, result)
        persisted = read_json(output)
        if persisted.get("real_submission_allowed") is not False:
            raise AssertionError("Persisted adapter report must forbid real submission")


def assert_invalid_preconditions_are_rejected() -> None:
    root = repo_root()
    request_jsonl = root / DEFAULT_FULL_TEXT_REQUEST_JSONL
    source_preconditions = read_json(root / DEFAULT_PRECONDITION_REPORT)
    bad_preconditions = copy.deepcopy(source_preconditions)
    bad_preconditions["status"] = "PRECONDITIONS_BLOCKED"
    bad_preconditions["failed_count"] = 1
    with tempfile.TemporaryDirectory() as temp_dir:
        bad_path = Path(temp_dir) / "bad_preconditions.json"
        write_json(bad_path, bad_preconditions)
        result = build_submission_adapter_report(
            request_jsonl_path=request_jsonl,
            precondition_report_path=bad_path,
            adapter_name="disabled",
        )
        if result.status != "REFUSED":
            raise AssertionError("Invalid preconditions must be refused")
        if result.reason != "DISABLED_ADAPTER_INPUTS_INVALID":
            raise AssertionError(f"Expected invalid-input refusal, got: {result.reason}")
        if not result.errors:
            raise AssertionError("Expected errors for invalid preconditions")
        if result.real_submission_allowed is not False:
            raise AssertionError("Invalid precondition refusal must forbid real submission")


def assert_unknown_adapter_fails_closed() -> None:
    try:
        get_embedding_submission_adapter("please-embed-on-friday")
    except ValueError as exc:
        if "Unsupported embedding submission adapter" not in str(exc):
            raise AssertionError(f"Unexpected unknown adapter error: {exc}") from exc
    else:
        raise AssertionError("Unknown adapter must fail closed")


def assert_no_response_or_vector_outputs_exist() -> None:
    root = repo_root()
    for relative in (DEFAULT_RESPONSE_JSONL, DEFAULT_VECTOR_PATH, DEFAULT_VECTOR_INDEX_PATH):
        if (root / relative).exists():
            raise AssertionError(f"Gate 18N must not create response/vector artifact: {relative}")


def main() -> None:
    assert_disabled_adapter_refuses_ready_preconditions()
    assert_invalid_preconditions_are_rejected()
    assert_unknown_adapter_fails_closed()
    assert_no_response_or_vector_outputs_exist()
    print("[gate18n:adapter] OK")
    print("[gate18n:adapter] disabled_adapter=refuses_submission")
    print("[gate18n:adapter] preconditions=validated")
    print("[gate18n:adapter] unknown_adapter=fail_closed")
    print("[gate18n:adapter] real_submission_allowed=false")
    print("[gate18n:adapter] vectors=not_created")


if __name__ == "__main__":
    main()
