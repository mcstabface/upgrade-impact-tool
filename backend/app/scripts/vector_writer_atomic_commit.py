from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.vector_writer_dry_run_validator import vector_record_id_from_cache_key


DEFAULT_RESPONSE_FIXTURE_JSONL = "kbs/retrieval/kb_embedding_response_fixture.v1.jsonl"
DEFAULT_COMMIT_GATE_REPORT = "kbs/retrieval/kb_vector_writer_commit_gate.v1.json"
DEFAULT_VECTOR_PATH = "kbs/retrieval/kb_vectors.v1.jsonl"
DEFAULT_VECTOR_INDEX_PATH = "kbs/retrieval/kb_vector_index.v1.json"
DEFAULT_ATOMIC_COMMIT_REPORT = "kbs/retrieval/kb_vector_writer_atomic_commit_report.v1.json"


@dataclass(frozen=True)
class VectorRecord:
    vector_record_id: str
    chunk_id: str
    embedding_cache_key: str
    model: str
    dimensions: int
    vector: list[float]
    source_response_request_id: str
    status: str = "OK"


@dataclass(frozen=True)
class VectorIndexRecord:
    vector_record_id: str
    chunk_id: str
    embedding_cache_key: str
    dimensions: int
    offset: int


@dataclass(frozen=True)
class VectorAtomicCommitReport:
    report_version: str
    status: str
    source_response_fixture: str
    source_commit_gate_report: str
    vector_jsonl_path: str
    vector_index_path: str
    vector_count: int
    vector_file_sha256: str
    vector_index_sha256: str
    atomic_write: bool
    commit_gate_status: str
    errors: list[str] = field(default_factory=list)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object row: {path}")
        rows.append(payload)
    return rows


def validate_commit_gate(commit_gate_path: Path) -> dict[str, Any]:
    if not commit_gate_path.exists():
        raise FileNotFoundError(f"Commit gate report not found: {commit_gate_path}")
    gate = read_json(commit_gate_path)
    if gate.get("status") != "COMMIT_GATE_READY_BUT_DISABLED":
        raise ValueError(f"Commit gate status must be COMMIT_GATE_READY_BUT_DISABLED: {gate.get('status')}")
    if gate.get("failed_count") != 0:
        raise ValueError(f"Commit gate failed_count must be 0: {gate.get('failed_count')}")
    if gate.get("commit_enabled") is not False:
        raise ValueError("Gate 18R expects commit gate to be ready but explicitly disabled")
    if gate.get("vector_outputs_created") is not False:
        raise ValueError("Commit gate must not already claim vector outputs were created")
    return gate


def build_vector_records(response_fixture_path: Path) -> list[VectorRecord]:
    if not response_fixture_path.exists():
        raise FileNotFoundError(f"Response fixture not found: {response_fixture_path}")
    response_rows = read_jsonl(response_fixture_path)
    if not response_rows:
        raise ValueError("Response fixture must contain at least one row")
    records: list[VectorRecord] = []
    seen_vector_ids: set[str] = set()
    for index, row in enumerate(response_rows):
        request_id = str(row.get("request_id") or "")
        chunk_id = str(row.get("chunk_id") or "")
        cache_key = str(row.get("embedding_cache_key") or "")
        model = str(row.get("model") or "")
        dimensions = int(row.get("dimensions") or 0)
        vector = row.get("embedding_vector")
        if row.get("status") != "OK":
            raise ValueError(f"row[{index}] status must be OK")
        if not request_id or not chunk_id or not cache_key or not model:
            raise ValueError(f"row[{index}] missing required identity fields")
        if not isinstance(vector, list):
            raise ValueError(f"row[{index}] embedding_vector must be list")
        if len(vector) != dimensions:
            raise ValueError(f"row[{index}] embedding_vector length must match dimensions")
        clean_vector = [float(value) for value in vector]
        vector_record_id = vector_record_id_from_cache_key(cache_key)
        if vector_record_id in seen_vector_ids:
            raise ValueError(f"row[{index}] duplicate vector_record_id")
        seen_vector_ids.add(vector_record_id)
        records.append(
            VectorRecord(
                vector_record_id=vector_record_id,
                chunk_id=chunk_id,
                embedding_cache_key=cache_key,
                model=model,
                dimensions=dimensions,
                vector=clean_vector,
                source_response_request_id=request_id,
            )
        )
    return records


def build_index_records(records: list[VectorRecord]) -> list[VectorIndexRecord]:
    return [
        VectorIndexRecord(
            vector_record_id=record.vector_record_id,
            chunk_id=record.chunk_id,
            embedding_cache_key=record.embedding_cache_key,
            dimensions=record.dimensions,
            offset=index,
        )
        for index, record in enumerate(records)
    ]


def atomic_write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_name(path.name + ".tmp")
    temp_path.write_text(content, encoding="utf-8")
    os.replace(temp_path, path)


def write_vector_outputs_atomic(*, vector_path: Path, index_path: Path, records: list[VectorRecord]) -> None:
    index_records = build_index_records(records)
    vector_content = "\n".join(json.dumps(asdict(record), sort_keys=True) for record in records) + "\n"
    index_payload = {
        "index_version": "1",
        "vector_count": len(index_records),
        "vector_jsonl_path": str(vector_path.relative_to(repo_root())) if vector_path.is_relative_to(repo_root()) else str(vector_path),
        "records": [asdict(record) for record in index_records],
    }
    index_content = json.dumps(index_payload, indent=2, sort_keys=True) + "\n"
    atomic_write_text(vector_path, vector_content)
    atomic_write_text(index_path, index_content)


def build_atomic_commit_report(
    *,
    response_fixture_path: Path,
    commit_gate_path: Path,
    vector_path: Path,
    index_path: Path,
) -> VectorAtomicCommitReport:
    gate = validate_commit_gate(commit_gate_path)
    records = build_vector_records(response_fixture_path)
    write_vector_outputs_atomic(vector_path=vector_path, index_path=index_path, records=records)
    root = repo_root()
    return VectorAtomicCommitReport(
        report_version="1",
        status="VECTOR_OUTPUTS_COMMITTED_FROM_FIXTURE",
        source_response_fixture=str(response_fixture_path.relative_to(root)) if response_fixture_path.is_relative_to(root) else str(response_fixture_path),
        source_commit_gate_report=str(commit_gate_path.relative_to(root)) if commit_gate_path.is_relative_to(root) else str(commit_gate_path),
        vector_jsonl_path=str(vector_path.relative_to(root)) if vector_path.is_relative_to(root) else str(vector_path),
        vector_index_path=str(index_path.relative_to(root)) if index_path.is_relative_to(root) else str(index_path),
        vector_count=len(records),
        vector_file_sha256=sha256_file(vector_path),
        vector_index_sha256=sha256_file(index_path),
        atomic_write=True,
        commit_gate_status=str(gate.get("status")),
        errors=[],
    )


def write_atomic_commit_report(path: Path, report: VectorAtomicCommitReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Commit Gate 18R fixture vectors using atomic writes.")
    parser.add_argument("--response-fixture", type=Path, default=root / DEFAULT_RESPONSE_FIXTURE_JSONL)
    parser.add_argument("--commit-gate", type=Path, default=root / DEFAULT_COMMIT_GATE_REPORT)
    parser.add_argument("--vector-output", type=Path, default=root / DEFAULT_VECTOR_PATH)
    parser.add_argument("--index-output", type=Path, default=root / DEFAULT_VECTOR_INDEX_PATH)
    parser.add_argument("--report-output", type=Path, default=root / DEFAULT_ATOMIC_COMMIT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_atomic_commit_report(
        response_fixture_path=args.response_fixture,
        commit_gate_path=args.commit_gate,
        vector_path=args.vector_output,
        index_path=args.index_output,
    )
    write_atomic_commit_report(args.report_output, report)
    print(f"[gate18r:atomic-vector] Wrote vector JSONL: {args.vector_output}")
    print(f"[gate18r:atomic-vector] Wrote vector index: {args.index_output}")
    print(f"[gate18r:atomic-vector] Wrote atomic commit report: {args.report_output}")
    print(f"[gate18r:atomic-vector] vector_count={report.vector_count}")
    print("[gate18r:atomic-vector] atomic_write=true")


if __name__ == "__main__":
    main()
