from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.vector_artifact_retrieval_readiness import (
    DEFAULT_ATOMIC_COMMIT_REPORT,
    DEFAULT_VECTOR_INDEX_PATH,
    DEFAULT_VECTOR_PATH,
    build_vector_retrieval_readiness_report,
    read_json,
    read_jsonl,
    write_vector_retrieval_readiness_report,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def assert_current_artifacts_are_ready() -> None:
    root = repo_root()
    vector_path = root / DEFAULT_VECTOR_PATH
    index_path = root / DEFAULT_VECTOR_INDEX_PATH
    atomic_report = root / DEFAULT_ATOMIC_COMMIT_REPORT
    if not vector_path.exists():
        raise AssertionError(f"Expected vector JSONL: {vector_path}")
    if not index_path.exists():
        raise AssertionError(f"Expected vector index: {index_path}")
    if not atomic_report.exists():
        raise AssertionError(f"Expected atomic commit report: {atomic_report}")
    report = build_vector_retrieval_readiness_report(
        vector_path=vector_path,
        index_path=index_path,
        atomic_commit_report_path=atomic_report,
    )
    if report.status != "RETRIEVAL_READY":
        raise AssertionError(f"Expected RETRIEVAL_READY, got: {report.status} blockers={report.blockers}")
    if report.retrieval_ready is not True:
        raise AssertionError("retrieval_ready must be true")
    if report.vector_count != 3:
        raise AssertionError(f"Expected 3 vectors, got: {report.vector_count}")
    if report.dimensions <= 0:
        raise AssertionError("Expected positive dimensions")
    if report.failed_count != 0:
        raise AssertionError(f"Expected zero failed checks, got: {report.failed_count}")
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "readiness.json"
        write_vector_retrieval_readiness_report(output, report)
        persisted = read_json(output)
        if persisted.get("status") != "RETRIEVAL_READY":
            raise AssertionError("Persisted report status mismatch")


def assert_corrupt_index_blocks_readiness() -> None:
    root = repo_root()
    vector_rows = read_jsonl(root / DEFAULT_VECTOR_PATH)
    index_payload = read_json(root / DEFAULT_VECTOR_INDEX_PATH)
    atomic_report = read_json(root / DEFAULT_ATOMIC_COMMIT_REPORT)
    corrupt_index = copy.deepcopy(index_payload)
    records = corrupt_index.get("records")
    if not isinstance(records, list) or not records:
        raise AssertionError("Expected index records")
    records.reverse()
    with tempfile.TemporaryDirectory() as temp_dir:
        vector_path = Path(temp_dir) / "kb_vectors.v1.jsonl"
        index_path = Path(temp_dir) / "kb_vector_index.v1.json"
        report_path = Path(temp_dir) / "atomic.json"
        write_jsonl(vector_path, vector_rows)
        write_json(index_path, corrupt_index)
        write_json(report_path, atomic_report)
        report = build_vector_retrieval_readiness_report(
            vector_path=vector_path,
            index_path=index_path,
            atomic_commit_report_path=report_path,
        )
        if report.status != "RETRIEVAL_NOT_READY":
            raise AssertionError(f"Expected not ready for corrupt index, got: {report.status}")
        if "vector_index_order_matches" not in report.blockers:
            raise AssertionError(f"Expected order blocker, got: {report.blockers}")


def assert_corrupt_vector_dimension_blocks_readiness() -> None:
    root = repo_root()
    vector_rows = read_jsonl(root / DEFAULT_VECTOR_PATH)
    index_payload = read_json(root / DEFAULT_VECTOR_INDEX_PATH)
    atomic_report = read_json(root / DEFAULT_ATOMIC_COMMIT_REPORT)
    corrupt_vectors = copy.deepcopy(vector_rows)
    corrupt_vectors[0]["vector"] = corrupt_vectors[0]["vector"][:-1]
    with tempfile.TemporaryDirectory() as temp_dir:
        vector_path = Path(temp_dir) / "kb_vectors.v1.jsonl"
        index_path = Path(temp_dir) / "kb_vector_index.v1.json"
        report_path = Path(temp_dir) / "atomic.json"
        write_jsonl(vector_path, corrupt_vectors)
        write_json(index_path, index_payload)
        write_json(report_path, atomic_report)
        report = build_vector_retrieval_readiness_report(
            vector_path=vector_path,
            index_path=index_path,
            atomic_commit_report_path=report_path,
        )
        if report.status != "RETRIEVAL_NOT_READY":
            raise AssertionError(f"Expected not ready for corrupt vector, got: {report.status}")
        if "vector_lengths_match_dimensions" not in report.blockers:
            raise AssertionError(f"Expected vector length blocker, got: {report.blockers}")


def main() -> None:
    assert_current_artifacts_are_ready()
    assert_corrupt_index_blocks_readiness()
    assert_corrupt_vector_dimension_blocks_readiness()
    print("[gate18s:readiness] OK")
    print("[gate18s:readiness] current_artifacts=retrieval_ready")
    print("[gate18s:readiness] corrupt_index=not_ready")
    print("[gate18s:readiness] corrupt_vector=not_ready")
    print("[gate18s:readiness] checksums=validated")


if __name__ == "__main__":
    main()
