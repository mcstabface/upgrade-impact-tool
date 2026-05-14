from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_RESPONSE_FIXTURE_JSONL = "kbs/retrieval/kb_embedding_response_fixture.v1.jsonl"
DEFAULT_VECTOR_DRY_RUN_REPORT = "kbs/retrieval/kb_vector_writer_dry_run_report.v1.json"
DEFAULT_VECTOR_PATH = "kbs/retrieval/kb_vectors.v1.jsonl"
DEFAULT_VECTOR_INDEX_PATH = "kbs/retrieval/kb_vector_index.v1.json"


@dataclass(frozen=True)
class VectorDryRunRecord:
    vector_record_id: str
    chunk_id: str
    embedding_cache_key: str
    model: str
    dimensions: int
    source_response_request_id: str
    status: str = "OK"


@dataclass(frozen=True)
class VectorDryRunReport:
    report_version: str
    status: str
    source_response_fixture: str
    candidate_vector_count: int
    validation_error_count: int
    validation_errors: list[str]
    candidate_vectors: list[VectorDryRunRecord] = field(default_factory=list)
    vector_jsonl_path: str = DEFAULT_VECTOR_PATH
    vector_index_path: str = DEFAULT_VECTOR_INDEX_PATH
    vector_outputs_created: bool = False
    dry_run_only: bool = True


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


def vector_record_id_from_cache_key(cache_key: str) -> str:
    return "vec_" + hashlib.sha256(f"vector:{cache_key}".encode("utf-8")).hexdigest()[:32]


def validate_response_rows(response_rows: list[dict[str, Any]]) -> tuple[list[VectorDryRunRecord], list[str]]:
    errors: list[str] = []
    records: list[VectorDryRunRecord] = []
    seen_vector_ids: set[str] = set()
    seen_cache_keys: set[str] = set()
    for index, row in enumerate(response_rows):
        request_id = str(row.get("request_id") or "")
        chunk_id = str(row.get("chunk_id") or "")
        cache_key = str(row.get("embedding_cache_key") or "")
        model = str(row.get("model") or "")
        status = str(row.get("status") or "")
        dimensions = int(row.get("dimensions") or 0)
        vector = row.get("embedding_vector")
        prefix = f"row[{index}]"
        if status != "OK":
            errors.append(f"{prefix}: response status must be OK")
        if not request_id:
            errors.append(f"{prefix}: request_id is required")
        if not chunk_id:
            errors.append(f"{prefix}: chunk_id is required")
        if not cache_key:
            errors.append(f"{prefix}: embedding_cache_key is required")
        if not model:
            errors.append(f"{prefix}: model is required")
        if dimensions <= 0:
            errors.append(f"{prefix}: dimensions must be positive")
        if not isinstance(vector, list):
            errors.append(f"{prefix}: embedding_vector must be a list")
        elif len(vector) != dimensions:
            errors.append(f"{prefix}: embedding_vector length must match dimensions")
        elif not all(isinstance(value, (float, int)) for value in vector):
            errors.append(f"{prefix}: embedding_vector values must be numeric")
        if cache_key in seen_cache_keys:
            errors.append(f"{prefix}: duplicate embedding_cache_key")
        seen_cache_keys.add(cache_key)
        vector_record_id = vector_record_id_from_cache_key(cache_key)
        if vector_record_id in seen_vector_ids:
            errors.append(f"{prefix}: duplicate vector_record_id")
        seen_vector_ids.add(vector_record_id)
        records.append(
            VectorDryRunRecord(
                vector_record_id=vector_record_id,
                chunk_id=chunk_id,
                embedding_cache_key=cache_key,
                model=model,
                dimensions=dimensions,
                source_response_request_id=request_id,
            )
        )
    return records, errors


def build_vector_writer_dry_run_report(*, response_fixture_path: Path) -> VectorDryRunReport:
    if not response_fixture_path.exists():
        raise FileNotFoundError(f"Response fixture not found: {response_fixture_path}")
    response_rows = read_jsonl(response_fixture_path)
    records, errors = validate_response_rows(response_rows)
    root = repo_root()
    source_response_fixture = str(response_fixture_path.relative_to(root)) if response_fixture_path.is_relative_to(root) else str(response_fixture_path)
    return VectorDryRunReport(
        report_version="1",
        status="DRY_RUN_VALID" if not errors else "DRY_RUN_INVALID",
        source_response_fixture=source_response_fixture,
        candidate_vector_count=len(records),
        validation_error_count=len(errors),
        validation_errors=errors,
        candidate_vectors=records if not errors else [],
        vector_outputs_created=False,
        dry_run_only=True,
    )


def write_vector_writer_dry_run_report(path: Path, report: VectorDryRunReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate vector writer behavior in dry-run only.")
    parser.add_argument("--response-fixture", type=Path, default=root / DEFAULT_RESPONSE_FIXTURE_JSONL)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_VECTOR_DRY_RUN_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_vector_writer_dry_run_report(response_fixture_path=args.response_fixture)
    write_vector_writer_dry_run_report(args.output, report)
    print(f"[gate18p:vector-dry-run] Wrote vector writer dry-run report: {args.output}")
    print(f"[gate18p:vector-dry-run] status={report.status}")
    print(f"[gate18p:vector-dry-run] candidate_vector_count={report.candidate_vector_count}")
    print(f"[gate18p:vector-dry-run] validation_error_count={report.validation_error_count}")
    print("[gate18p:vector-dry-run] vector_outputs_created=false")


if __name__ == "__main__":
    main()
