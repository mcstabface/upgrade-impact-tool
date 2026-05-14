from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_QUERY_REPORT = "kbs/retrieval/kb_fixture_vector_similarity_query.v1.json"
DEFAULT_REQUEST_JSONL = "kbs/retrieval/kb_embedding_full_text_requests.v1.jsonl"
DEFAULT_CITATION_JOIN_REPORT = "kbs/retrieval/kb_fixture_vector_citation_join.v1.json"


@dataclass(frozen=True)
class VectorCitationJoinResult:
    rank: int
    vector_record_id: str
    chunk_id: str
    embedding_cache_key: str
    score: float
    request_id: str
    citation_payload: dict[str, Any]
    text_hash: str


@dataclass(frozen=True)
class VectorCitationJoinReport:
    report_version: str
    status: str
    source_query_report: str
    source_request_jsonl: str
    result_count: int
    joined_count: int
    missing_citation_count: int
    results: list[VectorCitationJoinResult] = field(default_factory=list)
    production_retrieval_enabled: bool = False


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


def request_rows_by_chunk_id(request_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_chunk_id: dict[str, dict[str, Any]] = {}
    for row in request_rows:
        chunk_id = str(row.get("chunk_id") or "")
        if not chunk_id:
            raise ValueError("Request row missing chunk_id")
        if chunk_id in by_chunk_id:
            raise ValueError(f"Duplicate request chunk_id: {chunk_id}")
        by_chunk_id[chunk_id] = row
    return by_chunk_id


def build_vector_citation_join_report(*, query_report_path: Path, request_jsonl_path: Path) -> VectorCitationJoinReport:
    if not query_report_path.exists():
        raise FileNotFoundError(f"Query report not found: {query_report_path}")
    if not request_jsonl_path.exists():
        raise FileNotFoundError(f"Request JSONL not found: {request_jsonl_path}")
    query_report = read_json(query_report_path)
    if query_report.get("status") != "FIXTURE_VECTOR_QUERY_OK":
        raise ValueError(f"Query report status must be FIXTURE_VECTOR_QUERY_OK: {query_report.get('status')}")
    if query_report.get("production_retrieval_enabled") is not False:
        raise ValueError("Query report must keep production_retrieval_enabled false")
    query_results = query_report.get("results")
    if not isinstance(query_results, list):
        raise ValueError("Query report results must be a list")
    request_by_chunk_id = request_rows_by_chunk_id(read_jsonl(request_jsonl_path))

    joined: list[VectorCitationJoinResult] = []
    missing_citation_count = 0
    for result in query_results:
        if not isinstance(result, dict):
            raise ValueError("Query result must be an object")
        chunk_id = str(result.get("chunk_id") or "")
        request_row = request_by_chunk_id.get(chunk_id)
        if request_row is None:
            raise ValueError(f"No request row found for query result chunk_id: {chunk_id}")
        citation_payload = request_row.get("citation_payload") or {}
        if not isinstance(citation_payload, dict) or not citation_payload:
            missing_citation_count += 1
        joined.append(
            VectorCitationJoinResult(
                rank=int(result.get("rank") or 0),
                vector_record_id=str(result.get("vector_record_id") or ""),
                chunk_id=chunk_id,
                embedding_cache_key=str(result.get("embedding_cache_key") or ""),
                score=float(result.get("score") or 0.0),
                request_id=str(request_row.get("request_id") or ""),
                citation_payload=citation_payload,
                text_hash=str(request_row.get("text_hash") or ""),
            )
        )
    root = repo_root()
    status = "CITATION_JOIN_OK" if missing_citation_count == 0 else "CITATION_JOIN_MISSING_PAYLOADS"
    return VectorCitationJoinReport(
        report_version="1",
        status=status,
        source_query_report=str(query_report_path.relative_to(root)) if query_report_path.is_relative_to(root) else str(query_report_path),
        source_request_jsonl=str(request_jsonl_path.relative_to(root)) if request_jsonl_path.is_relative_to(root) else str(request_jsonl_path),
        result_count=len(query_results),
        joined_count=len(joined),
        missing_citation_count=missing_citation_count,
        results=joined,
        production_retrieval_enabled=False,
    )


def write_vector_citation_join_report(path: Path, report: VectorCitationJoinReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Join fixture vector query results to citation payloads.")
    parser.add_argument("--query-report", type=Path, default=root / DEFAULT_QUERY_REPORT)
    parser.add_argument("--request-jsonl", type=Path, default=root / DEFAULT_REQUEST_JSONL)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_CITATION_JOIN_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_vector_citation_join_report(query_report_path=args.query_report, request_jsonl_path=args.request_jsonl)
    write_vector_citation_join_report(args.output, report)
    print(f"[gate18u:citation-join] Wrote citation join report: {args.output}")
    print(f"[gate18u:citation-join] status={report.status}")
    print(f"[gate18u:citation-join] result_count={report.result_count}")
    print(f"[gate18u:citation-join] joined_count={report.joined_count}")
    print(f"[gate18u:citation-join] missing_citation_count={report.missing_citation_count}")
    print("[gate18u:citation-join] production_retrieval_enabled=false")


if __name__ == "__main__":
    main()
