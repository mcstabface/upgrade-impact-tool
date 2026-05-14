from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_VECTOR_PATH = "kbs/retrieval/kb_vectors.v1.jsonl"
DEFAULT_VECTOR_READINESS_REPORT = "kbs/retrieval/kb_vector_retrieval_readiness.v1.json"
DEFAULT_QUERY_REPORT = "kbs/retrieval/kb_fixture_vector_similarity_query.v1.json"


@dataclass(frozen=True)
class FixtureVectorSearchResult:
    rank: int
    vector_record_id: str
    chunk_id: str
    embedding_cache_key: str
    score: float


@dataclass(frozen=True)
class FixtureVectorSimilarityQueryReport:
    report_version: str
    status: str
    source_vector_jsonl: str
    source_readiness_report: str
    query_vector_record_id: str
    top_k: int
    result_count: int
    results: list[FixtureVectorSearchResult] = field(default_factory=list)
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


def cosine_similarity(left: list[float], right: list[float]) -> float:
    if len(left) != len(right):
        raise ValueError("Vectors must have identical dimensions")
    dot = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    if left_norm == 0 or right_norm == 0:
        raise ValueError("Zero-length vector norm is not allowed")
    return dot / (left_norm * right_norm)


def validate_readiness(readiness_report_path: Path) -> None:
    if not readiness_report_path.exists():
        raise FileNotFoundError(f"Vector readiness report not found: {readiness_report_path}")
    readiness = read_json(readiness_report_path)
    if readiness.get("status") != "RETRIEVAL_READY" or readiness.get("retrieval_ready") is not True:
        raise ValueError("Vector artifacts are not retrieval-ready")


def load_vectors_by_id(vector_path: Path) -> dict[str, dict[str, Any]]:
    if not vector_path.exists():
        raise FileNotFoundError(f"Vector JSONL not found: {vector_path}")
    rows = read_jsonl(vector_path)
    by_id: dict[str, dict[str, Any]] = {}
    for row in rows:
        vector_id = str(row.get("vector_record_id") or "")
        if not vector_id:
            raise ValueError("Vector row missing vector_record_id")
        if vector_id in by_id:
            raise ValueError(f"Duplicate vector_record_id: {vector_id}")
        vector = row.get("vector")
        dimensions = int(row.get("dimensions") or 0)
        if not isinstance(vector, list) or len(vector) != dimensions:
            raise ValueError(f"Vector length mismatch: {vector_id}")
        by_id[vector_id] = row
    return by_id


def build_similarity_query_report(
    *,
    vector_path: Path,
    readiness_report_path: Path,
    query_vector_record_id: str | None,
    top_k: int,
) -> FixtureVectorSimilarityQueryReport:
    if top_k <= 0:
        raise ValueError("top_k must be positive")
    validate_readiness(readiness_report_path)
    vectors_by_id = load_vectors_by_id(vector_path)
    if not vectors_by_id:
        raise ValueError("No vectors available")
    selected_query_id = query_vector_record_id or sorted(vectors_by_id)[0]
    query_row = vectors_by_id.get(selected_query_id)
    if query_row is None:
        raise ValueError(f"Unknown query vector_record_id: {selected_query_id}")
    query_vector = [float(value) for value in query_row["vector"]]
    scored: list[tuple[float, str, dict[str, Any]]] = []
    for vector_id, row in vectors_by_id.items():
        candidate_vector = [float(value) for value in row["vector"]]
        score = cosine_similarity(query_vector, candidate_vector)
        scored.append((score, vector_id, row))
    scored.sort(key=lambda item: (-item[0], item[1]))
    results = [
        FixtureVectorSearchResult(
            rank=index + 1,
            vector_record_id=vector_id,
            chunk_id=str(row.get("chunk_id") or ""),
            embedding_cache_key=str(row.get("embedding_cache_key") or ""),
            score=round(score, 12),
        )
        for index, (score, vector_id, row) in enumerate(scored[:top_k])
    ]
    root = repo_root()
    return FixtureVectorSimilarityQueryReport(
        report_version="1",
        status="FIXTURE_VECTOR_QUERY_OK",
        source_vector_jsonl=str(vector_path.relative_to(root)) if vector_path.is_relative_to(root) else str(vector_path),
        source_readiness_report=str(readiness_report_path.relative_to(root)) if readiness_report_path.is_relative_to(root) else str(readiness_report_path),
        query_vector_record_id=selected_query_id,
        top_k=top_k,
        result_count=len(results),
        results=results,
        production_retrieval_enabled=False,
    )


def write_similarity_query_report(path: Path, report: FixtureVectorSimilarityQueryReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run fixture vector similarity query.")
    parser.add_argument("--vector-jsonl", type=Path, default=root / DEFAULT_VECTOR_PATH)
    parser.add_argument("--readiness-report", type=Path, default=root / DEFAULT_VECTOR_READINESS_REPORT)
    parser.add_argument("--query-vector-record-id", default=None)
    parser.add_argument("--top-k", type=int, default=3)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_QUERY_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_similarity_query_report(
        vector_path=args.vector_jsonl,
        readiness_report_path=args.readiness_report,
        query_vector_record_id=args.query_vector_record_id,
        top_k=args.top_k,
    )
    write_similarity_query_report(args.output, report)
    print(f"[gate18t:similarity] Wrote fixture vector query report: {args.output}")
    print(f"[gate18t:similarity] status={report.status}")
    print(f"[gate18t:similarity] query_vector_record_id={report.query_vector_record_id}")
    print(f"[gate18t:similarity] result_count={report.result_count}")
    print("[gate18t:similarity] production_retrieval_enabled=false")


if __name__ == "__main__":
    main()
