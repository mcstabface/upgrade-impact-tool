from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.citation_bound_vector_context_assembly import (
    DEFAULT_CITATION_JOIN_REPORT,
    build_citation_bound_vector_context,
    read_json,
    write_citation_bound_vector_context,
)
from app.scripts.extract_kb_source_manifest import repo_root


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_current_context_assembles() -> None:
    root = repo_root()
    citation_join = root / DEFAULT_CITATION_JOIN_REPORT
    if not citation_join.exists():
        raise AssertionError(f"Expected Gate 18U citation join report: {citation_join}")
    report = build_citation_bound_vector_context(citation_join_report_path=citation_join)
    if report.status != "CITATION_BOUND_VECTOR_CONTEXT_READY":
        raise AssertionError(f"Unexpected context status: {report.status}")
    if report.context_item_count != 3:
        raise AssertionError(f"Expected 3 context items, got: {report.context_item_count}")
    if report.production_retrieval_enabled is not False:
        raise AssertionError("Production retrieval must remain disabled")
    if report.impact_generation_enabled is not False:
        raise AssertionError("Impact generation must remain disabled")
    ranks = [item.rank for item in report.context_items]
    if ranks != [1, 2, 3]:
        raise AssertionError(f"Unexpected context ranks: {ranks}")
    for item in report.context_items:
        if not item.citation_label.startswith(f"vector-rank-{item.rank}:"):
            raise AssertionError(f"Unexpected citation label: {item.citation_label}")
        if not item.source_artifact_path:
            raise AssertionError(f"Missing source artifact path: {item}")
        if not item.kb_document_id or not item.bug_patch_number or not item.child_sha256:
            raise AssertionError(f"Missing citation trace field: {item}")
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "context.json"
        write_citation_bound_vector_context(output, report)
        persisted = read_json(output)
        if persisted.get("impact_generation_enabled") is not False:
            raise AssertionError("Persisted context must not enable impact generation")


def assert_bad_join_status_refuses_context() -> None:
    root = repo_root()
    source = read_json(root / DEFAULT_CITATION_JOIN_REPORT)
    bad = copy.deepcopy(source)
    bad["status"] = "CITATION_JOIN_MISSING_PAYLOADS"
    with tempfile.TemporaryDirectory() as temp_dir:
        bad_path = Path(temp_dir) / "bad_join.json"
        write_json(bad_path, bad)
        try:
            build_citation_bound_vector_context(citation_join_report_path=bad_path)
        except ValueError as exc:
            if "CITATION_JOIN_OK" not in str(exc):
                raise AssertionError(f"Unexpected refusal reason: {exc}") from exc
        else:
            raise AssertionError("Bad citation join status must refuse context assembly")


def assert_missing_trace_field_refuses_context() -> None:
    root = repo_root()
    source = read_json(root / DEFAULT_CITATION_JOIN_REPORT)
    bad = copy.deepcopy(source)
    results = bad.get("results")
    if not isinstance(results, list) or not results or not isinstance(results[0], dict):
        raise AssertionError("Expected citation join results")
    results[0]["child_sha256"] = ""
    with tempfile.TemporaryDirectory() as temp_dir:
        bad_path = Path(temp_dir) / "missing_trace.json"
        write_json(bad_path, bad)
        try:
            build_citation_bound_vector_context(citation_join_report_path=bad_path)
        except ValueError as exc:
            if "missing required fields" not in str(exc):
                raise AssertionError(f"Unexpected missing-field refusal: {exc}") from exc
        else:
            raise AssertionError("Missing citation trace must refuse context assembly")


def main() -> None:
    assert_current_context_assembles()
    assert_bad_join_status_refuses_context()
    assert_missing_trace_field_refuses_context()
    print("[gate18v:context] OK")
    print("[gate18v:context] context_items=valid")
    print("[gate18v:context] citation_trace=complete")
    print("[gate18v:context] bad_join=fail_closed")
    print("[gate18v:context] impact_generation_enabled=false")


if __name__ == "__main__":
    main()
