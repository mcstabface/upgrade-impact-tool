from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.vector_writer_atomic_commit import (
    DEFAULT_COMMIT_GATE_REPORT,
    DEFAULT_RESPONSE_FIXTURE_JSONL,
    build_atomic_commit_report,
    read_json,
    read_jsonl,
    write_atomic_commit_report,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_atomic_commit_writes_consistent_outputs() -> None:
    root = repo_root()
    response_fixture = root / DEFAULT_RESPONSE_FIXTURE_JSONL
    commit_gate = root / DEFAULT_COMMIT_GATE_REPORT
    if not response_fixture.exists():
        raise AssertionError(f"Expected Gate 18O response fixture: {response_fixture}")
    if not commit_gate.exists():
        raise AssertionError(f"Expected Gate 18Q commit gate report: {commit_gate}")
    with tempfile.TemporaryDirectory() as temp_dir:
        vector_path = Path(temp_dir) / "kb_vectors.v1.jsonl"
        index_path = Path(temp_dir) / "kb_vector_index.v1.json"
        report_path = Path(temp_dir) / "atomic_report.json"
        report = build_atomic_commit_report(
            response_fixture_path=response_fixture,
            commit_gate_path=commit_gate,
            vector_path=vector_path,
            index_path=index_path,
        )
        write_atomic_commit_report(report_path, report)
        if report.status != "VECTOR_OUTPUTS_COMMITTED_FROM_FIXTURE":
            raise AssertionError(f"Unexpected report status: {report.status}")
        if report.vector_count != 3:
            raise AssertionError(f"Expected 3 vectors, got: {report.vector_count}")
        if report.atomic_write is not True:
            raise AssertionError("Report must mark atomic_write true")
        if not vector_path.exists() or not index_path.exists():
            raise AssertionError("Expected vector and index outputs")
        vector_rows = read_jsonl(vector_path)
        index_payload = read_json(index_path)
        if len(vector_rows) != report.vector_count:
            raise AssertionError("Vector row count mismatch")
        if index_payload.get("vector_count") != report.vector_count:
            raise AssertionError("Index vector count mismatch")
        index_records = index_payload.get("records")
        if not isinstance(index_records, list):
            raise AssertionError("Index records must be a list")
        vector_ids = [row.get("vector_record_id") for row in vector_rows]
        index_ids = [row.get("vector_record_id") for row in index_records if isinstance(row, dict)]
        if vector_ids != index_ids:
            raise AssertionError("Vector/index ID ordering mismatch")
        for row in vector_rows:
            vector = row.get("vector")
            dimensions = row.get("dimensions")
            if not isinstance(vector, list) or len(vector) != dimensions:
                raise AssertionError("Vector row dimension mismatch")
        persisted = read_json(report_path)
        if persisted.get("vector_file_sha256") != report.vector_file_sha256:
            raise AssertionError("Persisted report vector checksum mismatch")


def assert_blocked_commit_gate_refuses_without_outputs() -> None:
    root = repo_root()
    response_fixture = root / DEFAULT_RESPONSE_FIXTURE_JSONL
    commit_gate_source = read_json(root / DEFAULT_COMMIT_GATE_REPORT)
    blocked_gate = copy.deepcopy(commit_gate_source)
    blocked_gate["status"] = "COMMIT_GATE_BLOCKED"
    blocked_gate["failed_count"] = 1
    with tempfile.TemporaryDirectory() as temp_dir:
        blocked_gate_path = Path(temp_dir) / "blocked_gate.json"
        vector_path = Path(temp_dir) / "kb_vectors.v1.jsonl"
        index_path = Path(temp_dir) / "kb_vector_index.v1.json"
        write_json(blocked_gate_path, blocked_gate)
        try:
            build_atomic_commit_report(
                response_fixture_path=response_fixture,
                commit_gate_path=blocked_gate_path,
                vector_path=vector_path,
                index_path=index_path,
            )
        except ValueError as exc:
            if "COMMIT_GATE_READY_BUT_DISABLED" not in str(exc):
                raise AssertionError(f"Unexpected refusal reason: {exc}") from exc
        else:
            raise AssertionError("Expected blocked commit gate to refuse vector writes")
        if vector_path.exists() or index_path.exists():
            raise AssertionError("Blocked commit gate must not write outputs")


def assert_invalid_fixture_refuses_without_outputs() -> None:
    root = repo_root()
    commit_gate = root / DEFAULT_COMMIT_GATE_REPORT
    fixture_rows = read_jsonl(root / DEFAULT_RESPONSE_FIXTURE_JSONL)
    fixture_rows[0]["embedding_vector"] = fixture_rows[0]["embedding_vector"][:-1]
    with tempfile.TemporaryDirectory() as temp_dir:
        bad_fixture = Path(temp_dir) / "bad_fixture.jsonl"
        vector_path = Path(temp_dir) / "kb_vectors.v1.jsonl"
        index_path = Path(temp_dir) / "kb_vector_index.v1.json"
        bad_fixture.write_text("\n".join(json.dumps(row, sort_keys=True) for row in fixture_rows) + "\n", encoding="utf-8")
        try:
            build_atomic_commit_report(
                response_fixture_path=bad_fixture,
                commit_gate_path=commit_gate,
                vector_path=vector_path,
                index_path=index_path,
            )
        except ValueError as exc:
            if "length must match dimensions" not in str(exc):
                raise AssertionError(f"Unexpected invalid fixture reason: {exc}") from exc
        else:
            raise AssertionError("Expected invalid fixture to refuse vector writes")
        if vector_path.exists() or index_path.exists():
            raise AssertionError("Invalid fixture must not write outputs")


def main() -> None:
    assert_atomic_commit_writes_consistent_outputs()
    assert_blocked_commit_gate_refuses_without_outputs()
    assert_invalid_fixture_refuses_without_outputs()
    print("[gate18r:atomic-vector] OK")
    print("[gate18r:atomic-vector] atomic_outputs=valid")
    print("[gate18r:atomic-vector] index_consistency=valid")
    print("[gate18r:atomic-vector] blocked_gate=fail_closed")
    print("[gate18r:atomic-vector] invalid_fixture=fail_closed")


if __name__ == "__main__":
    main()
