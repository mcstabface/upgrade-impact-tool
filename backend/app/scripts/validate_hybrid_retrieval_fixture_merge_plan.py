from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.hybrid_retrieval_design_contract import (
    DEFAULT_HYBRID_RETRIEVAL_CONTRACT,
    build_hybrid_retrieval_design_contract,
    write_hybrid_retrieval_design_contract,
)
from app.scripts.hybrid_retrieval_fixture_merge_plan import (
    build_fixture_merge_plan,
    read_json,
    write_fixture_merge_plan,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_merge_plan_preserves_boundaries() -> None:
    root = repo_root()
    design_contract = root / DEFAULT_HYBRID_RETRIEVAL_CONTRACT
    if not design_contract.exists():
        write_hybrid_retrieval_design_contract(design_contract, build_hybrid_retrieval_design_contract())
    plan = build_fixture_merge_plan(design_contract_path=design_contract)
    if plan.status != "HYBRID_RETRIEVAL_FIXTURE_MERGE_PLAN_READY":
        raise AssertionError(f"Unexpected merge plan status: {plan.status}")
    if plan.bm25_authoritative is not True:
        raise AssertionError("BM25 must remain authoritative")
    if plan.vector_retrieval_authoritative is not False:
        raise AssertionError("Vector retrieval must not be authoritative")
    if plan.hybrid_merge_enabled is not False:
        raise AssertionError("Hybrid merge must remain disabled")
    if plan.production_semantic_retrieval_enabled is not False:
        raise AssertionError("Production semantic retrieval must remain disabled")
    if plan.score_normalization_enabled is not False:
        raise AssertionError("Score normalization must remain disabled")
    if plan.reranking_enabled is not False:
        raise AssertionError("Reranking must remain disabled")
    if plan.citation_preservation_required is not True:
        raise AssertionError("Citation preservation must be required")
    if plan.merge_output_mode != "disabled_plan_only":
        raise AssertionError(f"Unexpected merge output mode: {plan.merge_output_mode}")
    rules = {rule.name: rule for rule in plan.merge_rules}
    if "preserve_citation_payloads" not in rules or rules["preserve_citation_payloads"].enabled is not True:
        raise AssertionError("Citation preservation rule must be enabled")
    if "disable_output_merge" not in rules or rules["disable_output_merge"].enabled is not True:
        raise AssertionError("Output merge disable rule must be enabled")
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "merge_plan.json"
        write_fixture_merge_plan(output, plan)
        persisted = read_json(output)
        if persisted.get("hybrid_merge_enabled") is not False:
            raise AssertionError("Persisted merge plan must keep hybrid merge disabled")


def assert_bad_design_contract_blocks_plan() -> None:
    source_contract = build_hybrid_retrieval_design_contract()
    payload = json.loads(json.dumps(source_contract, default=lambda value: value.__dict__))
    bad_cases = [
        ("status", "HYBRID_RETRIEVAL_DESIGN_CONTRACT_BLOCKED"),
        ("bm25_authoritative", False),
        ("vector_retrieval_fixture_only", False),
        ("hybrid_merge_enabled", True),
    ]
    for field_name, bad_value in bad_cases:
        bad = copy.deepcopy(payload)
        bad[field_name] = bad_value
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_path = Path(temp_dir) / f"bad_{field_name}.json"
            write_json(bad_path, bad)
            try:
                build_fixture_merge_plan(design_contract_path=bad_path)
            except ValueError:
                continue
            raise AssertionError(f"Bad design contract field must block merge plan: {field_name}")


def main() -> None:
    assert_merge_plan_preserves_boundaries()
    assert_bad_design_contract_blocks_plan()
    print("[gate19b:merge-plan] OK")
    print("[gate19b:merge-plan] bm25_authoritative=preserved")
    print("[gate19b:merge-plan] vector_retrieval=diagnostic_only")
    print("[gate19b:merge-plan] hybrid_merge_enabled=false")
    print("[gate19b:merge-plan] citation_preservation=required")


if __name__ == "__main__":
    main()
