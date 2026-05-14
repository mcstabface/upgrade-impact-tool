from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_FULL_TEXT_REQUEST_JSONL = "kbs/retrieval/kb_embedding_full_text_requests.v1.jsonl"
DEFAULT_RESPONSE_FIXTURE_JSONL = "kbs/retrieval/kb_embedding_response_fixture.v1.jsonl"
DEFAULT_VECTOR_WRITER_DESIGN = "kbs/retrieval/kb_embedding_vector_writer_design.v1.json"
DEFAULT_VECTOR_PATH = "kbs/retrieval/kb_vectors.v1.jsonl"
DEFAULT_VECTOR_INDEX_PATH = "kbs/retrieval/kb_vector_index.v1.json"
DEFAULT_DIMENSIONS = 1536
FIXTURE_ROW_LIMIT = 3


@dataclass(frozen=True)
class EmbeddingResponseFixtureRow:
    request_id: str
    chunk_id: str
    embedding_cache_key: str
    model: str
    dimensions: int
    embedding_vector: list[float]
    status: str = "OK"
    error: str | None = None


@dataclass(frozen=True)
class VectorWriterDesignReport:
    report_version: str
    status: str
    source_request_jsonl: str
    response_fixture_jsonl: str
    fixture_response_count: int
    vector_jsonl_path: str
    vector_index_path: str
    row_contract: dict[str, str]
    validation_rules: list[str]
    vector_outputs_created: bool = False
    real_submission_allowed: bool = False
    dry_run_only: bool = True
    notes: list[str] = field(default_factory=list)


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


def deterministic_fixture_vector(seed: str, dimensions: int = DEFAULT_DIMENSIONS) -> list[float]:
    values: list[float] = []
    counter = 0
    while len(values) < dimensions:
        digest = hashlib.sha256(f"{seed}:{counter}".encode("utf-8")).digest()
        for byte in digest:
            values.append(round((byte / 255.0) * 2.0 - 1.0, 6))
            if len(values) == dimensions:
                break
        counter += 1
    return values


def build_response_fixture_rows(*, request_jsonl_path: Path, limit: int = FIXTURE_ROW_LIMIT) -> list[EmbeddingResponseFixtureRow]:
    if not request_jsonl_path.exists():
        raise FileNotFoundError(f"Request JSONL not found: {request_jsonl_path}")
    request_rows = read_jsonl(request_jsonl_path)
    if not request_rows:
        raise ValueError("Request JSONL must contain at least one row")
    fixture_rows: list[EmbeddingResponseFixtureRow] = []
    for row in request_rows[:limit]:
        request_id = str(row.get("request_id") or "")
        chunk_id = str(row.get("chunk_id") or "")
        cache_key = str(row.get("embedding_cache_key") or "")
        model = str(row.get("model") or "")
        dimensions = int(row.get("dimensions") or DEFAULT_DIMENSIONS)
        if not request_id or not chunk_id or not cache_key or not model:
            raise ValueError(f"Request row missing required fields: {row}")
        fixture_rows.append(
            EmbeddingResponseFixtureRow(
                request_id=request_id,
                chunk_id=chunk_id,
                embedding_cache_key=cache_key,
                model=model,
                dimensions=dimensions,
                embedding_vector=deterministic_fixture_vector(cache_key, dimensions=dimensions),
            )
        )
    return fixture_rows


def write_response_fixture_jsonl(path: Path, rows: list[EmbeddingResponseFixtureRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(asdict(row), sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def build_vector_writer_design_report(*, request_jsonl_path: Path, response_fixture_path: Path, rows: list[EmbeddingResponseFixtureRow]) -> VectorWriterDesignReport:
    root = repo_root()
    source_request_jsonl = str(request_jsonl_path.relative_to(root)) if request_jsonl_path.is_relative_to(root) else str(request_jsonl_path)
    response_fixture_jsonl = str(response_fixture_path.relative_to(root)) if response_fixture_path.is_relative_to(root) else str(response_fixture_path)
    return VectorWriterDesignReport(
        report_version="1",
        status="DESIGN_ONLY_VECTOR_WRITER_NOT_ENABLED",
        source_request_jsonl=source_request_jsonl,
        response_fixture_jsonl=response_fixture_jsonl,
        fixture_response_count=len(rows),
        vector_jsonl_path=DEFAULT_VECTOR_PATH,
        vector_index_path=DEFAULT_VECTOR_INDEX_PATH,
        row_contract={
            "vector_record_id": "string",
            "chunk_id": "string",
            "embedding_cache_key": "string",
            "model": "string",
            "dimensions": "integer",
            "vector": "array<float>",
            "source_response_request_id": "string",
            "status": "OK",
        },
        validation_rules=[
            "response status must be OK",
            "embedding vector length must match dimensions",
            "embedding_cache_key must match request manifest cache key",
            "chunk_id must match source request row",
            "vector_record_id must be deterministic from embedding_cache_key",
            "duplicate vector_record_id values are forbidden",
            "vector writer must fail before partial vector output on validation error",
        ],
        vector_outputs_created=False,
        real_submission_allowed=False,
        dry_run_only=True,
        notes=[
            "Gate 18O writes a small deterministic response fixture only.",
            "Gate 18O does not write vector JSONL or vector index artifacts.",
        ],
    )


def write_vector_writer_design_report(path: Path, report: VectorWriterDesignReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build Gate 18O embedding response fixture and vector writer design report.")
    parser.add_argument("--request-jsonl", type=Path, default=root / DEFAULT_FULL_TEXT_REQUEST_JSONL)
    parser.add_argument("--response-fixture-output", type=Path, default=root / DEFAULT_RESPONSE_FIXTURE_JSONL)
    parser.add_argument("--design-output", type=Path, default=root / DEFAULT_VECTOR_WRITER_DESIGN)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    rows = build_response_fixture_rows(request_jsonl_path=args.request_jsonl)
    write_response_fixture_jsonl(args.response_fixture_output, rows)
    report = build_vector_writer_design_report(
        request_jsonl_path=args.request_jsonl,
        response_fixture_path=args.response_fixture_output,
        rows=rows,
    )
    write_vector_writer_design_report(args.design_output, report)
    print(f"[gate18o:vector-design] Wrote response fixture: {args.response_fixture_output}")
    print(f"[gate18o:vector-design] Wrote vector writer design: {args.design_output}")
    print(f"[gate18o:vector-design] fixture_response_count={len(rows)}")
    print("[gate18o:vector-design] vector_writer=design_only")
    print("[gate18o:vector-design] vectors=not_created")


if __name__ == "__main__":
    main()
