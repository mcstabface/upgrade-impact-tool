from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.hybrid_retrieval_fixture_merge_plan import (
    DEFAULT_FIXTURE_MERGE_PLAN,
    build_fixture_merge_plan,
    write_fixture_merge_plan,
)
from app.scripts.hybrid_retrieval_score_normalization_design import (
    build_score_normalization_design,
    read_json,
    write_score_normalization_design,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_score_design_preserves_boundaries() -> None:
    root = repo_root()
    merge_plan = root / DEFAULT_FIXTURE_MERGE_PLAN
    if not merge_plan.exists():
        write_fixture_merge_plan(
            merge_plan,
            build_fixture_merge_plan(design_contract_path=root / "kbs" / "retrieval" / "kb_hybrid_retrieval_design_contract.v1.json"),
        )
    design = build_score_normalization_design(fixture_merge_plan_path=merge_plan)
    if design.status != "HYBRID_SCORE_NORMALIZATION_DESIGN_READY":
        raise AssertionError(f"Unexpected design status: {design.status}")
    if design.score_normalization_enabled is not False:
        raise AssertionError("Score normalization must remain disabled")
    if design.normalization_design_only is not True:
        raise AssertionError("Normalization must be design-only")
    if design.hybrid_merge_enabled is not False:
        raise AssertionError("Hybrid merge must remain disabled")
    if design.reranking_enabled is not False:
        raise AssertionError("Reranking must remain disabled")
    if design.production_semantic_retrieval_enabled is not False:
        raise AssertionError("Production semantic retrieval must remain disabled")
    if design.bm25_authoritative is not True:
        raise AssertionError("BM25 must remain authoritative")
    if design.vector_retrieval_authoritative is not False:
        raise AssertionError("Vector retrieval must not be authoritative")
    if design.normalized_scores_written is not False:
        raise AssertionError("Normalized scores must not be written")
    if design.merged_results_written is not False:
        raise AssertionError("Merged results must not be written")
    if len(design.formulas) != 3:
        raise AssertionError(f"Expected three design formulas, got: {len(design.formulas)}")
    for formula in design.formulas:
        if formula.enabled is not False:
            raise AssertionError(f"Formula must remain disabled: {formula.name}")
        if not formula.formula:
            raise AssertionError(f"Formula text missing: {formula.name}")
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "score_design.json"
        write_score_normalization_design(output, design)
        persisted = read_json(output)
        if persisted.get("normalized_scores_written") is not False:
            raise AssertionError("Persisted design must not write normalized scores")


def assert_bad_merge_plan_blocks_design() -> None:
    root = repo_root()
    merge_plan = root / DEFAULT_FIXTURE_MERGE_PLAN
    if not merge_plan.exists():
        write_fixture_merge_plan(
            merge_plan,
            build_fixture_merge_plan(design_contract_path=root / "kbs" / "retrieval" / "kb_hybrid_retrieval_design_contract.v1.json"),
        )
    source = read_json(merge_plan)
    bad_cases = [
        ("status", "HYBRID_RETRIEVAL_FIXTURE_MERGE_PLAN_BLOCKED"),
        ("hybrid_merge_enabled", True),
        ("bm25_authoritative", False),
        ("vector_retrieval_authoritative", True),
    ]
    for field_name, bad_value in bad_cases:
        bad = copy.deepcopy(source)
        bad[field_name] = bad_value
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_path = Path(temp_dir) / f"bad_{field_name}.json"
            write_json(bad_path, bad)
            try:
                build_score_normalization_design(fixture_merge_plan_path=bad_path)
            except ValueError:
                continue
            raise AssertionError(f"Bad merge plan field must block score design: {field_name}")


def main() -> None:
    assert_score_design_preserves_boundaries()
    assert_bad_merge_plan_blocks_design()
    print("[gate19c:score-design] OK")
    print("[gate19c:score-design] formulas=specified_not_enabled")
    print("[gate19c:score-design] normalized_scores_written=false")
    print("[gate19c:score-design] hybrid_merge_enabled=false")
    print("[gate19c:score-design] merged_results_written=false")


if __name__ == "__main__":
    main()
