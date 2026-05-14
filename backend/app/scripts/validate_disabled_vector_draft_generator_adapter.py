from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.disabled_vector_draft_generator_adapter import (
    DEFAULT_DRAFT_OUTPUT_REPORT,
    DEFAULT_GENERATION_CONTRACT_REPORT,
    build_disabled_generator_report,
    get_vector_draft_generator_adapter,
    read_json,
    write_disabled_generator_report,
)
from app.scripts.extract_kb_source_manifest import repo_root


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_disabled_adapter_refuses_ready_contract() -> None:
    root = repo_root()
    contract = root / DEFAULT_GENERATION_CONTRACT_REPORT
    result = build_disabled_generator_report(generation_contract_path=contract, adapter_name="disabled")
    if result.status != "REFUSED":
        raise AssertionError(f"Disabled adapter must refuse, got: {result.status}")
    if result.reason != "DISABLED_ADAPTER_REFUSES_DRAFT_GENERATION":
        raise AssertionError(f"Unexpected refusal reason: {result.reason}")
    if result.errors:
        raise AssertionError(f"Expected no input errors for ready contract, got: {result.errors}")
    if result.would_generate is not False:
        raise AssertionError("Disabled adapter must not indicate would_generate")
    if result.draft_generation_enabled is not False:
        raise AssertionError("Draft generation must remain disabled")
    if result.llm_call_allowed is not False:
        raise AssertionError("LLM call must not be allowed")
    if result.llm_call_performed is not False:
        raise AssertionError("LLM call must not be performed")
    if result.generated_text != "":
        raise AssertionError("Disabled adapter must not generate text")
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "disabled_generator.json"
        write_disabled_generator_report(output, result)
        persisted = read_json(output)
        if persisted.get("generated_text") != "":
            raise AssertionError("Persisted disabled generator report must not contain text")


def assert_invalid_contract_is_refused_as_invalid() -> None:
    root = repo_root()
    source_contract = root / DEFAULT_GENERATION_CONTRACT_REPORT
    build_disabled_generator_report(generation_contract_path=source_contract, adapter_name="disabled")
    source = read_json(source_contract)
    bad = copy.deepcopy(source)
    bad["status"] = "GENERATION_CONTRACT_BLOCKED"
    bad["failed_count"] = 1
    with tempfile.TemporaryDirectory() as temp_dir:
        bad_contract = Path(temp_dir) / "bad_contract.json"
        write_json(bad_contract, bad)
        result = build_disabled_generator_report(generation_contract_path=bad_contract, adapter_name="disabled")
        if result.status != "REFUSED":
            raise AssertionError("Invalid contract must be refused")
        if result.reason != "DISABLED_ADAPTER_INPUTS_INVALID":
            raise AssertionError(f"Expected invalid-input refusal, got: {result.reason}")
        if not result.errors:
            raise AssertionError("Expected validation errors for invalid contract")
        if result.llm_call_performed is not False:
            raise AssertionError("Invalid contract must not perform LLM call")


def assert_unknown_adapter_fails_closed() -> None:
    try:
        get_vector_draft_generator_adapter("please-generate-the-prose")
    except ValueError as exc:
        if "Unsupported vector draft generator adapter" not in str(exc):
            raise AssertionError(f"Unexpected unknown adapter error: {exc}") from exc
    else:
        raise AssertionError("Unknown generator adapter must fail closed")


def assert_no_draft_output_exists() -> None:
    draft_output = repo_root() / DEFAULT_DRAFT_OUTPUT_REPORT
    if draft_output.exists():
        raise AssertionError(f"Gate 18Z must not create generated draft output: {draft_output}")


def main() -> None:
    assert_disabled_adapter_refuses_ready_contract()
    assert_invalid_contract_is_refused_as_invalid()
    assert_unknown_adapter_fails_closed()
    assert_no_draft_output_exists()
    print("[gate18z:disabled-generator] OK")
    print("[gate18z:disabled-generator] ready_contract=refused")
    print("[gate18z:disabled-generator] invalid_contract=fail_closed")
    print("[gate18z:disabled-generator] unknown_adapter=fail_closed")
    print("[gate18z:disabled-generator] llm_call_performed=false")


if __name__ == "__main__":
    main()
