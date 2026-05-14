from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_VECTOR_PATH = "kbs/retrieval/kb_vectors.v1.jsonl"
DEFAULT_VECTOR_INDEX_PATH = "kbs/retrieval/kb_vector_index.v1.json"
DEFAULT_ATOMIC_COMMIT_REPORT = "kbs/retrieval/kb_vector_writer_atomic_commit_report.v1.json"
DEFAULT_RETRIEVAL_READINESS_REPORT = "kbs/retrieval/kb_vector_retrieval_readiness.v1.json"


@dataclass(frozen=True)
class VectorReadinessCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class VectorRetrievalReadinessReport:
    report_version: str
    status: str
    vector_jsonl_path: str
    vector_index_path: str
    atomic_commit_report_path: str
    vector_count: int
    dimensions: int
    vector_file_sha256: str
    vector_index_sha256: str
    checks: list[VectorReadinessCheck]
    passed_count: int
    failed_count: int
    retrieval_ready: bool
    blockers: list[str] = field(default_factory=list)


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


def build_vector_retrieval_readiness_report(
    *,
    vector_path: Path,
    index_path: Path,
    atomic_commit_report_path: Path,
) -> VectorRetrievalReadinessReport:
    checks: list[VectorReadinessCheck] = []
    blockers: list[str] = []

    def add_check(name: str, passed: bool, detail: str) -> None:
        checks.append(VectorReadinessCheck(name=name, passed=passed, detail=detail))
        if not passed:
            blockers.append(name)

    vector_rows: list[dict[str, Any]] = []
    index_payload: dict[str, Any] = {}
    atomic_report: dict[str, Any] = {}
    vector_sha = ""
    index_sha = ""

    add_check("vector_jsonl_exists", vector_path.exists(), str(vector_path))
    add_check("vector_index_exists", index_path.exists(), str(index_path))
    add_check("atomic_commit_report_exists", atomic_commit_report_path.exists(), str(atomic_commit_report_path))

    if vector_path.exists():
        vector_rows = read_jsonl(vector_path)
        vector_sha = sha256_file(vector_path)
    if index_path.exists():
        index_payload = read_json(index_path)
        index_sha = sha256_file(index_path)
    if atomic_commit_report_path.exists():
        atomic_report = read_json(atomic_commit_report_path)

    add_check("vector_rows_present", len(vector_rows) > 0, f"vector_rows={len(vector_rows)}")
    index_records = index_payload.get("records") if index_payload else None
    add_check("index_records_present", isinstance(index_records, list) and len(index_records) > 0, f"index_records={len(index_records) if isinstance(index_records, list) else 'missing'}")
    add_check("vector_count_matches_index", len(vector_rows) == int(index_payload.get("vector_count") or -1), f"vectors={len(vector_rows)} index_count={index_payload.get('vector_count')}")
    add_check("vector_count_matches_commit_report", len(vector_rows) == int(atomic_report.get("vector_count") or -1), f"vectors={len(vector_rows)} commit_count={atomic_report.get('vector_count')}")
    add_check("vector_checksum_matches_commit_report", vector_sha == str(atomic_report.get("vector_file_sha256") or ""), "vector sha256 comparison")
    add_check("index_checksum_matches_commit_report", index_sha == str(atomic_report.get("vector_index_sha256") or ""), "index sha256 comparison")

    vector_ids = [str(row.get("vector_record_id") or "") for row in vector_rows]
    index_ids = [str(row.get("vector_record_id") or "") for row in index_records] if isinstance(index_records, list) else []
    add_check("vector_ids_unique", len(vector_ids) == len(set(vector_ids)), f"unique={len(set(vector_ids))} total={len(vector_ids)}")
    add_check("vector_index_order_matches", vector_ids == index_ids, "vector IDs must match index order")

    dimensions = 0
    if vector_rows:
        first_dimensions = int(vector_rows[0].get("dimensions") or 0)
        dimensions = first_dimensions
        dimension_ok = first_dimensions > 0 and all(int(row.get("dimensions") or 0) == first_dimensions for row in vector_rows)
        vector_lengths_ok = all(isinstance(row.get("vector"), list) and len(row.get("vector")) == first_dimensions for row in vector_rows)
        status_ok = all(row.get("status") == "OK" for row in vector_rows)
    else:
        dimension_ok = False
        vector_lengths_ok = False
        status_ok = False
    add_check("dimensions_consistent", dimension_ok, f"dimensions={dimensions}")
    add_check("vector_lengths_match_dimensions", vector_lengths_ok, f"dimensions={dimensions}")
    add_check("vector_status_ok", status_ok, "all vector rows must have OK status")

    failed_count = sum(1 for check in checks if not check.passed)
    passed_count = len(checks) - failed_count
    root = repo_root()
    return VectorRetrievalReadinessReport(
        report_version="1",
        status="RETRIEVAL_READY" if failed_count == 0 else "RETRIEVAL_NOT_READY",
        vector_jsonl_path=str(vector_path.relative_to(root)) if vector_path.is_relative_to(root) else str(vector_path),
        vector_index_path=str(index_path.relative_to(root)) if index_path.is_relative_to(root) else str(index_path),
        atomic_commit_report_path=str(atomic_commit_report_path.relative_to(root)) if atomic_commit_report_path.is_relative_to(root) else str(atomic_commit_report_path),
        vector_count=len(vector_rows),
        dimensions=dimensions,
        vector_file_sha256=vector_sha,
        vector_index_sha256=index_sha,
        checks=checks,
        passed_count=passed_count,
        failed_count=failed_count,
        retrieval_ready=failed_count == 0,
        blockers=blockers,
    )


def write_vector_retrieval_readiness_report(path: Path, report: VectorRetrievalReadinessReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate vector artifacts and write retrieval readiness report.")
    parser.add_argument("--vector-jsonl", type=Path, default=root / DEFAULT_VECTOR_PATH)
    parser.add_argument("--vector-index", type=Path, default=root / DEFAULT_VECTOR_INDEX_PATH)
    parser.add_argument("--atomic-commit-report", type=Path, default=root / DEFAULT_ATOMIC_COMMIT_REPORT)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_RETRIEVAL_READINESS_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_vector_retrieval_readiness_report(
        vector_path=args.vector_jsonl,
        index_path=args.vector_index,
        atomic_commit_report_path=args.atomic_commit_report,
    )
    write_vector_retrieval_readiness_report(args.output, report)
    print(f"[gate18s:readiness] Wrote retrieval readiness report: {args.output}")
    print(f"[gate18s:readiness] status={report.status}")
    print(f"[gate18s:readiness] vector_count={report.vector_count}")
    print(f"[gate18s:readiness] dimensions={report.dimensions}")
    print(f"[gate18s:readiness] failed_checks={report.failed_count}")
    print(f"[gate18s:readiness] retrieval_ready={str(report.retrieval_ready).lower()}")


if __name__ == "__main__":
    main()
