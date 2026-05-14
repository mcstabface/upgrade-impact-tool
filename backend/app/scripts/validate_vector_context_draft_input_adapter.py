from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.vector_context_draft_input_adapter import (
    DEFAULT_VECTOR_CONTEXT_REPORT,
    build_vector_draft_input,
    read_json,
    write_vector_draft_input,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_current_context_adapts_to_draft_input() -> None:
    root = repo_root()
    vector_context = root / DEFAULT_VECTOR_CONTEXT_REPORT
    if not vector_context.exists():
        raise AssertionError(f"Expected Gate 18V vector context report: {vector_context}")
    report = build_vector_draft_input(vector_context_path=vector_context)
    if report.status != "VECTOR_DRAFT_INPUT_READY":
        raise AssertionError(f"Unexpected draft input status: {report.status}")
    if report.evidence_slot_count != 3:
        raise AssertionError(f"Expected 3 evidence slots, got: {report.evidence_slot_count}")
    if report.production_retrieval_enabled is not False:
        raise AssertionError("Production retrieval must remain disabled")
    if report.draft_generation_enabled is not False:
        raise AssertionError("Draft generation must remain disabled")
    ranks = [slot.rank for slot in report.evidence_slots]
    if ranks != [1, 2, 3]:
        raise AssertionError(f"Unexpected evidence ranks: {ranks}")
    for slot in report.evidence_slots:
        if slot.evidence_id != f"vector-evidence-{slot.rank:04d}":
            raise AssertionError(f"Unexpected evidence ID: {slot.evidence_id}")
        if not slot.citation_label:
            raise AssertionError(f"Missing citation label: {slot}")
        if not slot.source_artifact_path or not slot.child_sha256:
            raise AssertionError(f"Missing source trace: {slot}")
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "draft_input.json"
        write_vector_draft_input(output, report)
        persisted = read_json(output)
        if persisted.get("draft_generation_enabled") is not False:
            raise AssertionError("Persisted draft input must not enable draft generation")


def assert_bad_context_status_refuses_adapter() -> None:
    root = repo_root()
    source = read_json(root / DEFAULT_VECTOR_CONTEXT_REPORT)
    bad = copy.deepcopy(source)
    bad["status"] = "NOPE"
    with tempfile.TemporaryDirectory() as temp_dir:
        bad_path = Path(temp_dir) / "bad_context.json"
        write_json(bad_path, bad)
        try:
            build_vector_draft_input(vector_context_path=bad_path)
        except ValueError as exc:
            if "CITATION_BOUND_VECTOR_CONTEXT_READY" not in str(exc):
                raise AssertionError(f"Unexpected bad-status refusal: {exc}") from exc
        else:
            raise AssertionError("Bad context status must refuse draft input adaptation")


def assert_missing_context_trace_refuses_adapter() -> None:
    root = repo_root()
    source = read_json(root / DEFAULT_VECTOR_CONTEXT_REPORT)
    bad = copy.deepcopy(source)
    items = bad.get("context_items")
    if not isinstance(items, list) or not items or not isinstance(items[0], dict):
        raise AssertionError("Expected context items")
    items[0]["source_artifact_path"] = ""
    with tempfile.TemporaryDirectory() as temp_dir:
        bad_path = Path(temp_dir) / "missing_trace.json"
        write_json(bad_path, bad)
        try:
            build_vector_draft_input(vector_context_path=bad_path)
        except ValueError as exc:
            if "not draft-input ready" not in str(exc):
                raise AssertionError(f"Unexpected missing-trace refusal: {exc}") from exc
        else:
            raise AssertionError("Missing context trace must refuse draft input adaptation")


def main() -> None:
    assert_current_context_adapts_to_draft_input()
    assert_bad_context_status_refuses_adapter()
    assert_missing_context_trace_refuses_adapter()
    print("[gate18w:draft-input] OK")
    print("[gate18w:draft-input] evidence_slots=valid")
    print("[gate18w:draft-input] context_guard=fail_closed")
    print("[gate18w:draft-input] citation_trace=complete")
    print("[gate18w:draft-input] draft_generation_enabled=false")


if __name__ == "__main__":
    main()
