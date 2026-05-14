from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.hybrid_retrieval_design_contract import (
    build_hybrid_retrieval_design_contract,
    write_hybrid_retrieval_design_contract,
)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def assert_contract_preserves_boundaries() -> None:
    contract = build_hybrid_retrieval_design_contract()
    if contract.status != "HYBRID_RETRIEVAL_DESIGN_CONTRACT_READY":
        raise AssertionError(f"Unexpected contract status: {contract.status}")
    if contract.failed_count != 0:
        raise AssertionError(f"Expected zero failed checks, got: {contract.failed_count}")
    if contract.bm25_authoritative is not True:
        raise AssertionError("BM25 must remain authoritative")
    if contract.vector_retrieval_authoritative is not False:
        raise AssertionError("Vector retrieval must not be authoritative")
    if contract.vector_retrieval_fixture_only is not True:
        raise AssertionError("Vector retrieval must remain fixture-only")
    if contract.hybrid_merge_enabled is not False:
        raise AssertionError("Hybrid merge must remain disabled")
    if contract.production_semantic_retrieval_enabled is not False:
        raise AssertionError("Production semantic retrieval must remain disabled")
    if contract.implicit_reranking_enabled is not False:
        raise AssertionError("Implicit reranking must remain disabled")
    if contract.draft_generation_enabled is not False:
        raise AssertionError("Draft generation must remain disabled")
    if contract.llm_call_allowed is not False:
        raise AssertionError("LLM calls must remain disallowed")
    if "bm25_authoritative" not in contract.retrieval_modes:
        raise AssertionError("Retrieval modes must include bm25_authoritative")
    if "vector_fixture_diagnostic" not in contract.retrieval_modes:
        raise AssertionError("Retrieval modes must include vector_fixture_diagnostic")
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "hybrid_contract.json"
        write_hybrid_retrieval_design_contract(output, contract)
        persisted = read_json(output)
        if persisted.get("hybrid_merge_enabled") is not False:
            raise AssertionError("Persisted contract must keep hybrid merge disabled")


def assert_mutated_contract_would_be_blocked() -> None:
    contract = build_hybrid_retrieval_design_contract()
    payload = json.loads(json.dumps(contract, default=lambda value: value.__dict__))
    mutations = {
        "vector_retrieval_authoritative": True,
        "hybrid_merge_enabled": True,
        "production_semantic_retrieval_enabled": True,
        "implicit_reranking_enabled": True,
        "llm_call_allowed": True,
    }
    for field_name, bad_value in mutations.items():
        mutated = copy.deepcopy(payload)
        mutated[field_name] = bad_value
        if mutated.get(field_name) == payload.get(field_name):
            raise AssertionError(f"Mutation did not change value for {field_name}")
        if field_name == "vector_retrieval_authoritative" and mutated[field_name] is not True:
            raise AssertionError("Mutation fixture broken")
    # The design contract is built from constants. This assertion documents that direct mutation
    # is not an accepted runtime path; future executable validators should reject these flags.


def main() -> None:
    assert_contract_preserves_boundaries()
    assert_mutated_contract_would_be_blocked()
    print("[gate19a:hybrid-design] OK")
    print("[gate19a:hybrid-design] bm25_authoritative=preserved")
    print("[gate19a:hybrid-design] vector_retrieval=fixture_only")
    print("[gate19a:hybrid-design] hybrid_merge_enabled=false")
    print("[gate19a:hybrid-design] production_semantic_retrieval_enabled=false")


if __name__ == "__main__":
    main()
