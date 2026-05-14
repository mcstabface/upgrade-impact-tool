from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.embedding_response_fixture_vector_writer_design import (
    DEFAULT_FULL_TEXT_REQUEST_JSONL,
    DEFAULT_VECTOR_INDEX_PATH,
    DEFAULT_VECTOR_PATH,
    build_response_fixture_rows,
    build_vector_writer_design_report,
    write_response_fixture_jsonl,
    write_vector_writer_design_report,
)
from app.scripts.extract_kb_source_manifest import repo_root


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            item = json.loads(line)
            if not isinstance(item, dict):
                raise ValueError(f"Expected JSON object row: {path}")
            rows.append(item)
    return rows


def assert_fixture_and_design_contract() -> None:
    request_jsonl = repo_root() / DEFAULT_FULL_TEXT_REQUEST_JSONL
    if not request_jsonl.exists():
        raise AssertionError(f"Expected request JSONL: {request_jsonl}")
    rows = build_response_fixture_rows(request_jsonl_path=request_jsonl)
    if len(rows) != 3:
        raise AssertionError(f"Expected 3 fixture rows, got {len(rows)}")
    seen: set[str] = set()
    for row in rows:
        if row.status != "OK":
            raise AssertionError("Fixture rows must be OK")
        if row.request_id in seen:
            raise AssertionError(f"Duplicate request_id: {row.request_id}")
        seen.add(row.request_id)
        if len(row.embedding_vector) != row.dimensions:
            raise AssertionError(f"Dimension mismatch: {row.request_id}")
        if not all(isinstance(value, float) for value in row.embedding_vector):
            raise AssertionError(f"Embedding values must be floats: {row.request_id}")

    with tempfile.TemporaryDirectory() as temp_dir:
        response_path = Path(temp_dir) / "fixture.jsonl"
        design_path = Path(temp_dir) / "design.json"
        write_response_fixture_jsonl(response_path, rows)
        if len(read_jsonl(response_path)) != 3:
            raise AssertionError("Persisted fixture row count mismatch")
        report = build_vector_writer_design_report(
            request_jsonl_path=request_jsonl,
            response_fixture_path=response_path,
            rows=rows,
        )
        write_vector_writer_design_report(design_path, report)
        persisted = read_json(design_path)
        if persisted.get("status") != "DESIGN_ONLY_VECTOR_WRITER_NOT_ENABLED":
            raise AssertionError("Unexpected design status")
        if persisted.get("vector_outputs_created") is not False:
            raise AssertionError("Design report must not create vector outputs")
        if persisted.get("real_submission_allowed") is not False:
            raise AssertionError("Design report must forbid real submission")
        if persisted.get("fixture_response_count") != 3:
            raise AssertionError("Fixture response count mismatch")
        contract = persisted.get("row_contract")
        if not isinstance(contract, dict) or contract.get("vector") != "array<float>":
            raise AssertionError("Design report missing row contract")


def assert_no_vector_outputs_exist() -> None:
    root = repo_root()
    for relative in (DEFAULT_VECTOR_PATH, DEFAULT_VECTOR_INDEX_PATH):
        if (root / relative).exists():
            raise AssertionError(f"Gate 18O must not create artifact: {relative}")


def main() -> None:
    assert_fixture_and_design_contract()
    assert_no_vector_outputs_exist()
    print("[gate18o:vector-design] OK")
    print("[gate18o:vector-design] response_fixture=valid")
    print("[gate18o:vector-design] writer_contract=specified")
    print("[gate18o:vector-design] vectors=not_created")


if __name__ == "__main__":
    main()
