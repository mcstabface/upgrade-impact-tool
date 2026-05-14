from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.export_unresolved_redaction_review import (
    DEFAULT_REQUEST_JSONL,
    DEFAULT_REVIEW_EXPORT_JSON,
    DEFAULT_REVIEW_EXPORT_MD,
    DEFAULT_TRIAGE_REPORT,
    build_review_export,
    write_review_export_json,
    write_review_export_markdown,
)
from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_RESPONSE_JSONL = "kbs/retrieval/kb_embedding_batch_responses.v1.jsonl"
DEFAULT_VECTOR_PATH = "kbs/retrieval/kb_vectors.v1.jsonl"
DEFAULT_VECTOR_INDEX_PATH = "kbs/retrieval/kb_vector_index.v1.json"


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def assert_review_export_builds() -> None:
    root = repo_root()
    triage_report = root / DEFAULT_TRIAGE_REPORT
    request_jsonl = root / DEFAULT_REQUEST_JSONL
    if not triage_report.exists():
        raise AssertionError(f"Expected Gate 18H triage report: {triage_report}")
    if not request_jsonl.exists():
        raise AssertionError(f"Expected Gate 18F request JSONL: {request_jsonl}")

    triage = read_json(triage_report)
    expected_unresolved = int(triage.get("unresolved_finding_count") or 0)
    export = build_review_export(triage_report_path=triage_report, request_jsonl_path=request_jsonl)
    if export.unresolved_count != expected_unresolved:
        raise AssertionError(f"Unresolved count mismatch: {export.unresolved_count} vs {expected_unresolved}")
    if export.embedding_submission_allowed is not False:
        raise AssertionError("Review export must not allow embedding submission")
    if export.vectors_created is not False:
        raise AssertionError("Review export must not create vectors")
    if expected_unresolved > 0 and export.status != "REVIEW_REQUIRED":
        raise AssertionError(f"Expected REVIEW_REQUIRED status, got: {export.status}")
    if expected_unresolved == 0 and export.status != "NO_UNRESOLVED_FINDINGS":
        raise AssertionError(f"Expected NO_UNRESOLVED_FINDINGS status, got: {export.status}")
    for item in export.items:
        if item.reviewer_decision != "PENDING":
            raise AssertionError(f"Reviewer decision must default to PENDING: {item}")
        if not item.chunk_id:
            raise AssertionError(f"Review item missing chunk_id: {item}")
        if not item.context_window:
            raise AssertionError(f"Review item missing context window: {item}")
        if not item.citation_payload:
            raise AssertionError(f"Review item missing citation payload: {item}")

    with tempfile.TemporaryDirectory() as temp_dir:
        json_output = Path(temp_dir) / "review.json"
        markdown_output = Path(temp_dir) / "review.md"
        write_review_export_json(json_output, export)
        write_review_export_markdown(markdown_output, export)
        persisted = read_json(json_output)
        if persisted.get("unresolved_count") != expected_unresolved:
            raise AssertionError("Persisted unresolved count mismatch")
        if persisted.get("embedding_submission_allowed") is not False:
            raise AssertionError("Persisted export must forbid embedding submission")
        markdown = markdown_output.read_text(encoding="utf-8")
        if "| Review ID | Code | Classification | Matched Values | Context | Decision | Notes |" not in markdown:
            raise AssertionError("Markdown export missing review table")
        if "PENDING" not in markdown and expected_unresolved > 0:
            raise AssertionError("Markdown export should include pending decisions")


def assert_no_response_or_vector_outputs_exist() -> None:
    root = repo_root()
    for relative in (DEFAULT_RESPONSE_JSONL, DEFAULT_VECTOR_PATH, DEFAULT_VECTOR_INDEX_PATH):
        if (root / relative).exists():
            raise AssertionError(f"Gate 18J must not create response/vector artifact: {relative}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 18J unresolved redaction review export.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_review_export_builds()
    assert_no_response_or_vector_outputs_exist()
    print("[gate18j:review] OK")
    print("[gate18j:review] unresolved_findings=exported")
    print("[gate18j:review] reviewer_fields=pending")
    print("[gate18j:review] markdown_export=valid")
    print("[gate18j:review] embedding_submission=forbidden")
    print("[gate18j:review] vectors=not_created")


if __name__ == "__main__":
    main()
