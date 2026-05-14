from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.fixture_vector_similarity_query import (
    DEFAULT_QUERY_REPORT,
    DEFAULT_VECTOR_PATH,
    DEFAULT_VECTOR_READINESS_REPORT,
    build_similarity_query_report,
    cosine_similarity,
    read_json,
    write_similarity_query_report,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_cosine_similarity_identity() -> None:
    score = cosine_similarity([1.0, 0.0, 0.0], [1.0, 0.0, 0.0])
    if round(score, 12) != 1.0:
        raise AssertionError(f"Expected identity cosine 1.0, got: {score}")
    score = cosine_similarity([1.0, 0.0], [0.0, 1.0])
    if round(score, 12) != 0.0:
        raise AssertionError(f"Expected orthogonal cosine 0.0, got: {score}")


def assert_fixture_query_is_deterministic() -> None:
    root = repo_root()
    vector_path = root / DEFAULT_VECTOR_PATH
    readiness_report = root / DEFAULT_VECTOR_READINESS_REPORT
    if not vector_path.exists():
        raise AssertionError(f"Expected vector JSONL: {vector_path}")
    if not readiness_report.exists():
        raise AssertionError(f"Expected readiness report: {readiness_report}")
    report = build_similarity_query_report(
        vector_path=vector_path,
        readiness_report_path=readiness_report,
        query_vector_record_id=None,
        top_k=3,
    )
    if report.status != "FIXTURE_VECTOR_QUERY_OK":
        raise AssertionError(f"Unexpected query status: {report.status}")
    if report.production_retrieval_enabled is not False:
        raise AssertionError("Gate 18T must not enable production retrieval")
    if report.result_count != 3:
        raise AssertionError(f"Expected three results, got: {report.result_count}")
    if report.results[0].vector_record_id != report.query_vector_record_id:
        raise AssertionError("Top result should be the query vector itself")
    if report.results[0].score != 1.0:
        raise AssertionError(f"Expected self-similarity score 1.0, got: {report.results[0].score}")
    ranks = [result.rank for result in report.results]
    if ranks != [1, 2, 3]:
        raise AssertionError(f"Unexpected ranks: {ranks}")
    scores = [result.score for result in report.results]
    if scores != sorted(scores, reverse=True):
        raise AssertionError(f"Scores must be sorted descending: {scores}")
    repeat = build_similarity_query_report(
        vector_path=vector_path,
        readiness_report_path=readiness_report,
        query_vector_record_id=report.query_vector_record_id,
        top_k=3,
    )
    if [item.vector_record_id for item in repeat.results] != [item.vector_record_id for item in report.results]:
        raise AssertionError("Fixture query ordering must be deterministic")
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "query.json"
        write_similarity_query_report(output, report)
        persisted = read_json(output)
        if persisted.get("production_retrieval_enabled") is not False:
            raise AssertionError("Persisted query report must not enable production retrieval")


def assert_not_ready_report_refuses_query() -> None:
    root = repo_root()
    readiness = read_json(root / DEFAULT_VECTOR_READINESS_REPORT)
    not_ready = copy.deepcopy(readiness)
    not_ready["status"] = "RETRIEVAL_NOT_READY"
    not_ready["retrieval_ready"] = False
    with tempfile.TemporaryDirectory() as temp_dir:
        not_ready_path = Path(temp_dir) / "not_ready.json"
        write_json(not_ready_path, not_ready)
        try:
            build_similarity_query_report(
                vector_path=root / DEFAULT_VECTOR_PATH,
                readiness_report_path=not_ready_path,
                query_vector_record_id=None,
                top_k=3,
            )
        except ValueError as exc:
            if "not retrieval-ready" not in str(exc):
                raise AssertionError(f"Unexpected refusal reason: {exc}") from exc
        else:
            raise AssertionError("Expected not-ready readiness report to refuse query")


def assert_unknown_query_vector_refuses() -> None:
    root = repo_root()
    try:
        build_similarity_query_report(
            vector_path=root / DEFAULT_VECTOR_PATH,
            readiness_report_path=root / DEFAULT_VECTOR_READINESS_REPORT,
            query_vector_record_id="vec_missing",
            top_k=3,
        )
    except ValueError as exc:
        if "Unknown query vector_record_id" not in str(exc):
            raise AssertionError(f"Unexpected unknown-vector refusal: {exc}") from exc
    else:
        raise AssertionError("Unknown query vector must fail closed")


def main() -> None:
    assert_cosine_similarity_identity()
    assert_fixture_query_is_deterministic()
    assert_not_ready_report_refuses_query()
    assert_unknown_query_vector_refuses()
    print("[gate18t:similarity] OK")
    print("[gate18t:similarity] cosine=validated")
    print("[gate18t:similarity] fixture_query=deterministic")
    print("[gate18t:similarity] readiness_required=true")
    print("[gate18t:similarity] production_retrieval_enabled=false")


if __name__ == "__main__":
    main()
