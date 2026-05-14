from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.vector_query_result_citation_join import (
    DEFAULT_QUERY_REPORT,
    DEFAULT_REQUEST_JSONL,
    build_vector_citation_join_report,
    read_json,
    read_jsonl,
    write_vector_citation_join_report,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")


def assert_current_query_results_join_to_citations() -> None:
    root = repo_root()
    query_report = root / DEFAULT_QUERY_REPORT
    request_jsonl = root / DEFAULT_REQUEST_JSONL
    if not query_report.exists():
        raise AssertionError(f"Expected Gate 18T query report: {query_report}")
    if not request_jsonl.exists():
        raise AssertionError(f"Expected request JSONL: {request_jsonl}")
    report = build_vector_citation_join_report(query_report_path=query_report, request_jsonl_path=request_jsonl)
    if report.status != "CITATION_JOIN_OK":
        raise AssertionError(f"Expected citation join OK, got: {report.status}")
    if report.result_count != report.joined_count:
        raise AssertionError("Every query result must be joined")
    if report.missing_citation_count != 0:
        raise AssertionError("Expected zero missing citation payloads")
    if report.production_retrieval_enabled is not False:
        raise AssertionError("Gate 18U must not enable production retrieval")
    ranks = [result.rank for result in report.results]
    if ranks != sorted(ranks):
        raise AssertionError(f"Joined results must preserve rank order: {ranks}")
    for result in report.results:
        if not result.request_id:
            raise AssertionError(f"Joined result missing request_id: {result}")
        if not result.citation_payload:
            raise AssertionError(f"Joined result missing citation payload: {result}")
        if not result.source_artifact_path:
            raise AssertionError(f"Joined result missing source_artifact_path: {result}")
        if not result.kb_document_id:
            raise AssertionError(f"Joined result missing kb_document_id: {result}")
        if not result.bug_patch_number:
            raise AssertionError(f"Joined result missing bug_patch_number: {result}")
        if not result.child_sha256:
            raise AssertionError(f"Joined result missing child_sha256: {result}")
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "citation_join.json"
        write_vector_citation_join_report(output, report)
        persisted = read_json(output)
        if persisted.get("status") != "CITATION_JOIN_OK":
            raise AssertionError("Persisted join report status mismatch")
        if persisted.get("production_retrieval_enabled") is not False:
            raise AssertionError("Persisted join report must not enable production retrieval")


def assert_missing_citation_payload_is_reported() -> None:
    root = repo_root()
    request_rows = read_jsonl(root / DEFAULT_REQUEST_JSONL)
    query_report = root / DEFAULT_QUERY_REPORT
    query = read_json(query_report)
    results = query.get("results")
    if not isinstance(results, list) or not results:
        raise AssertionError("Expected query results")
    first_chunk_id = str(results[0].get("chunk_id") or "")
    modified_rows = copy.deepcopy(request_rows)
    for row in modified_rows:
        if row.get("chunk_id") == first_chunk_id:
            row["citation_payload"] = {}
            break
    else:
        raise AssertionError("Could not find query result chunk in request rows")

    with tempfile.TemporaryDirectory() as temp_dir:
        request_path = Path(temp_dir) / "requests.jsonl"
        write_jsonl(request_path, modified_rows)
        report = build_vector_citation_join_report(query_report_path=query_report, request_jsonl_path=request_path)
        if report.status != "CITATION_JOIN_MISSING_PAYLOADS":
            raise AssertionError(f"Expected missing payload status, got: {report.status}")
        if report.missing_citation_count != 1:
            raise AssertionError(f"Expected one missing citation payload, got: {report.missing_citation_count}")
        if report.production_retrieval_enabled is not False:
            raise AssertionError("Missing payload report must not enable production retrieval")


def assert_bad_query_status_refuses_join() -> None:
    root = repo_root()
    query = read_json(root / DEFAULT_QUERY_REPORT)
    bad_query = copy.deepcopy(query)
    bad_query["status"] = "NOPE"
    with tempfile.TemporaryDirectory() as temp_dir:
        query_path = Path(temp_dir) / "bad_query.json"
        write_json(query_path, bad_query)
        try:
            build_vector_citation_join_report(query_report_path=query_path, request_jsonl_path=root / DEFAULT_REQUEST_JSONL)
        except ValueError as exc:
            if "FIXTURE_VECTOR_QUERY_OK" not in str(exc):
                raise AssertionError(f"Unexpected refusal reason: {exc}") from exc
        else:
            raise AssertionError("Bad query status must refuse citation join")


def main() -> None:
    assert_current_query_results_join_to_citations()
    assert_missing_citation_payload_is_reported()
    assert_bad_query_status_refuses_join()
    print("[gate18u:citation-join] OK")
    print("[gate18u:citation-join] query_results=joined")
    print("[gate18u:citation-join] citations=present")
    print("[gate18u:citation-join] missing_citation=reported")
    print("[gate18u:citation-join] production_retrieval_enabled=false")


if __name__ == "__main__":
    main()
