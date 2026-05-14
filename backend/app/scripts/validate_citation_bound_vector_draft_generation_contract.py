from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.citation_bound_vector_draft_generation_contract import (
    DEFAULT_DRAFT_SKELETON_REPORT,
    build_generation_contract,
    read_json,
    write_generation_contract,
)
from app.scripts.extract_kb_source_manifest import repo_root


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_ready_skeleton_builds_disabled_contract() -> None:
    root = repo_root()
    skeleton = root / DEFAULT_DRAFT_SKELETON_REPORT
    if not skeleton.exists():
        raise AssertionError(f"Expected Gate 18X draft skeleton: {skeleton}")
    report = build_generation_contract(draft_skeleton_path=skeleton)
    if report.status != "GENERATION_DISABLED_CONTRACT_READY":
        raise AssertionError(f"Unexpected contract status: {report.status}")
    if report.failed_count != 0:
        raise AssertionError(f"Expected zero failed checks, got: {report.failed_count}")
    if report.generation_adapter != "disabled":
        raise AssertionError("Generation adapter must be disabled")
    if report.draft_generation_enabled is not False:
        raise AssertionError("Draft generation must remain disabled")
    if report.llm_call_allowed is not False:
        raise AssertionError("LLM calls must not be allowed")
    if report.llm_call_performed is not False:
        raise AssertionError("LLM calls must not be performed")
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "contract.json"
        write_generation_contract(output, report)
        persisted = read_json(output)
        if persisted.get("llm_call_allowed") is not False:
            raise AssertionError("Persisted contract must not allow LLM calls")


def assert_generation_enabled_skeleton_blocks_contract() -> None:
    root = repo_root()
    source = read_json(root / DEFAULT_DRAFT_SKELETON_REPORT)
    bad = copy.deepcopy(source)
    bad["draft_generation_enabled"] = True
    with tempfile.TemporaryDirectory() as temp_dir:
        bad_path = Path(temp_dir) / "generation_enabled.json"
        write_json(bad_path, bad)
        report = build_generation_contract(draft_skeleton_path=bad_path)
        if report.status != "GENERATION_CONTRACT_BLOCKED":
            raise AssertionError(f"Expected blocked status, got: {report.status}")
        if "draft_generation_disabled" not in report.blockers:
            raise AssertionError(f"Expected draft_generation_disabled blocker, got: {report.blockers}")
        if report.llm_call_allowed is not False:
            raise AssertionError("Blocked contract must not allow LLM calls")


def assert_generated_text_blocks_contract() -> None:
    root = repo_root()
    source = read_json(root / DEFAULT_DRAFT_SKELETON_REPORT)
    bad = copy.deepcopy(source)
    sections = bad.get("sections")
    if not isinstance(sections, list) or not sections or not isinstance(sections[0], dict):
        raise AssertionError("Expected skeleton sections")
    sections[0]["generated_text"] = "This should not be here."
    with tempfile.TemporaryDirectory() as temp_dir:
        bad_path = Path(temp_dir) / "generated_text.json"
        write_json(bad_path, bad)
        report = build_generation_contract(draft_skeleton_path=bad_path)
        if report.status != "GENERATION_CONTRACT_BLOCKED":
            raise AssertionError(f"Expected blocked status, got: {report.status}")
        if "generated_text_empty" not in report.blockers:
            raise AssertionError(f"Expected generated_text_empty blocker, got: {report.blockers}")


def main() -> None:
    assert_ready_skeleton_builds_disabled_contract()
    assert_generation_enabled_skeleton_blocks_contract()
    assert_generated_text_blocks_contract()
    print("[gate18y:generation-contract] OK")
    print("[gate18y:generation-contract] disabled_contract=ready")
    print("[gate18y:generation-contract] generation_enabled=blocked")
    print("[gate18y:generation-contract] generated_text=blocked")
    print("[gate18y:generation-contract] llm_call_allowed=false")


if __name__ == "__main__":
    main()
