from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.citation_bound_vector_draft_skeleton import (
    DEFAULT_DRAFT_INPUT_REPORT,
    build_citation_bound_vector_draft_skeleton,
    read_json,
    write_citation_bound_vector_draft_skeleton,
)
from app.scripts.extract_kb_source_manifest import repo_root


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_current_draft_skeleton_builds() -> None:
    root = repo_root()
    draft_input = root / DEFAULT_DRAFT_INPUT_REPORT
    if not draft_input.exists():
        raise AssertionError(f"Expected Gate 18W draft input: {draft_input}")
    report = build_citation_bound_vector_draft_skeleton(draft_input_path=draft_input)
    if report.status != "VECTOR_DRAFT_SKELETON_READY":
        raise AssertionError(f"Unexpected skeleton status: {report.status}")
    if report.evidence_slot_count != 3:
        raise AssertionError(f"Expected 3 evidence slots, got: {report.evidence_slot_count}")
    if report.section_count != 3:
        raise AssertionError(f"Expected 3 sections, got: {report.section_count}")
    if report.production_retrieval_enabled is not False:
        raise AssertionError("Production retrieval must remain disabled")
    if report.draft_generation_enabled is not False:
        raise AssertionError("Draft generation must remain disabled")
    if report.llm_call_performed is not False:
        raise AssertionError("Gate 18X must not perform an LLM call")
    sections_by_id = {section.section_id: section for section in report.sections}
    required_sections = {"vector-context-summary", "potential-upgrade-impact", "review-notes"}
    if set(sections_by_id) != required_sections:
        raise AssertionError(f"Unexpected sections: {set(sections_by_id)}")
    for section_id in ("vector-context-summary", "potential-upgrade-impact"):
        section = sections_by_id[section_id]
        if len(section.required_evidence_ids) != report.evidence_slot_count:
            raise AssertionError(f"Section missing evidence IDs: {section_id}")
        if len(section.citation_labels) != report.evidence_slot_count:
            raise AssertionError(f"Section missing citation labels: {section_id}")
        if section.generated_text != "":
            raise AssertionError(f"Section must not contain generated text: {section_id}")
    if sections_by_id["review-notes"].required_evidence_ids:
        raise AssertionError("Review notes section should not require evidence IDs")
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "skeleton.json"
        write_citation_bound_vector_draft_skeleton(output, report)
        persisted = read_json(output)
        if persisted.get("llm_call_performed") is not False:
            raise AssertionError("Persisted skeleton must not indicate LLM call")


def assert_bad_draft_input_status_refuses_skeleton() -> None:
    root = repo_root()
    source = read_json(root / DEFAULT_DRAFT_INPUT_REPORT)
    bad = copy.deepcopy(source)
    bad["status"] = "NOPE"
    with tempfile.TemporaryDirectory() as temp_dir:
        bad_path = Path(temp_dir) / "bad_input.json"
        write_json(bad_path, bad)
        try:
            build_citation_bound_vector_draft_skeleton(draft_input_path=bad_path)
        except ValueError as exc:
            if "VECTOR_DRAFT_INPUT_READY" not in str(exc):
                raise AssertionError(f"Unexpected status refusal: {exc}") from exc
        else:
            raise AssertionError("Bad draft input status must refuse skeleton build")


def assert_generation_enabled_input_refuses_skeleton() -> None:
    root = repo_root()
    source = read_json(root / DEFAULT_DRAFT_INPUT_REPORT)
    bad = copy.deepcopy(source)
    bad["draft_generation_enabled"] = True
    with tempfile.TemporaryDirectory() as temp_dir:
        bad_path = Path(temp_dir) / "generation_enabled.json"
        write_json(bad_path, bad)
        try:
            build_citation_bound_vector_draft_skeleton(draft_input_path=bad_path)
        except ValueError as exc:
            if "draft_generation_enabled false" not in str(exc):
                raise AssertionError(f"Unexpected generation flag refusal: {exc}") from exc
        else:
            raise AssertionError("Generation-enabled input must refuse skeleton build")


def main() -> None:
    assert_current_draft_skeleton_builds()
    assert_bad_draft_input_status_refuses_skeleton()
    assert_generation_enabled_input_refuses_skeleton()
    print("[gate18x:draft-skeleton] OK")
    print("[gate18x:draft-skeleton] sections=valid")
    print("[gate18x:draft-skeleton] evidence_bindings=valid")
    print("[gate18x:draft-skeleton] draft_generation_enabled=false")
    print("[gate18x:draft-skeleton] llm_call_performed=false")


if __name__ == "__main__":
    main()
