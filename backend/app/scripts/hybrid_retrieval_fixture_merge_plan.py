from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.hybrid_retrieval_design_contract import (
    DEFAULT_HYBRID_RETRIEVAL_CONTRACT,
    build_hybrid_retrieval_design_contract,
    write_hybrid_retrieval_design_contract,
)


DEFAULT_FIXTURE_MERGE_PLAN = "kbs/retrieval/kb_hybrid_retrieval_fixture_merge_plan.v1.json"


@dataclass(frozen=True)
class FixtureMergeRule:
    name: str
    enabled: bool
    detail: str


@dataclass(frozen=True)
class HybridRetrievalFixtureMergePlan:
    report_version: str
    status: str
    source_design_contract: str
    bm25_input_mode: str
    vector_input_mode: str
    merge_output_mode: str
    hybrid_merge_enabled: bool
    production_semantic_retrieval_enabled: bool
    bm25_authoritative: bool
    vector_retrieval_authoritative: bool
    score_normalization_enabled: bool
    reranking_enabled: bool
    citation_preservation_required: bool
    merge_rules: list[FixtureMergeRule] = field(default_factory=list)
    required_future_gates: list[str] = field(default_factory=list)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def ensure_design_contract(path: Path) -> None:
    if path.exists():
        return
    write_hybrid_retrieval_design_contract(path, build_hybrid_retrieval_design_contract())


def build_fixture_merge_plan(*, design_contract_path: Path) -> HybridRetrievalFixtureMergePlan:
    ensure_design_contract(design_contract_path)
    contract = read_json(design_contract_path)
    if contract.get("status") != "HYBRID_RETRIEVAL_DESIGN_CONTRACT_READY":
        raise ValueError(f"Hybrid retrieval design contract is not ready: {contract.get('status')}")
    if contract.get("bm25_authoritative") is not True:
        raise ValueError("Hybrid merge plan requires bm25_authoritative=true")
    if contract.get("vector_retrieval_fixture_only") is not True:
        raise ValueError("Hybrid merge plan requires vector_retrieval_fixture_only=true")
    if contract.get("hybrid_merge_enabled") is not False:
        raise ValueError("Gate 19B requires hybrid_merge_enabled=false")
    rules = [
        FixtureMergeRule(
            name="collect_bm25_authoritative_candidates",
            enabled=False,
            detail="Future gate will collect BM25 candidates as the authoritative baseline.",
        ),
        FixtureMergeRule(
            name="collect_vector_fixture_candidates",
            enabled=False,
            detail="Future gate will collect diagnostic vector fixture candidates only.",
        ),
        FixtureMergeRule(
            name="preserve_citation_payloads",
            enabled=True,
            detail="Any future merge must preserve citation payloads and source trace fields.",
        ),
        FixtureMergeRule(
            name="defer_score_normalization",
            enabled=True,
            detail="Score normalization is deferred to Gate 19C and must not happen implicitly.",
        ),
        FixtureMergeRule(
            name="disable_output_merge",
            enabled=True,
            detail="Gate 19B does not emit merged retrieval results.",
        ),
    ]
    root = repo_root()
    return HybridRetrievalFixtureMergePlan(
        report_version="1",
        status="HYBRID_RETRIEVAL_FIXTURE_MERGE_PLAN_READY",
        source_design_contract=str(design_contract_path.relative_to(root)) if design_contract_path.is_relative_to(root) else str(design_contract_path),
        bm25_input_mode="authoritative_baseline_planned",
        vector_input_mode="fixture_diagnostic_planned",
        merge_output_mode="disabled_plan_only",
        hybrid_merge_enabled=False,
        production_semantic_retrieval_enabled=False,
        bm25_authoritative=True,
        vector_retrieval_authoritative=False,
        score_normalization_enabled=False,
        reranking_enabled=False,
        citation_preservation_required=True,
        merge_rules=rules,
        required_future_gates=[
            "Gate 19C — Hybrid Retrieval Score Normalization Design",
            "Gate 19D — Hybrid Retrieval Citation Preservation Validator",
            "Gate 19E — Production Semantic Retrieval Enablement Gate",
        ],
    )


def write_fixture_merge_plan(path: Path, plan: HybridRetrievalFixtureMergePlan) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(plan), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build Gate 19B hybrid retrieval fixture merge plan.")
    parser.add_argument("--design-contract", type=Path, default=root / DEFAULT_HYBRID_RETRIEVAL_CONTRACT)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_FIXTURE_MERGE_PLAN)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plan = build_fixture_merge_plan(design_contract_path=args.design_contract)
    write_fixture_merge_plan(args.output, plan)
    print(f"[gate19b:merge-plan] Wrote hybrid retrieval fixture merge plan: {args.output}")
    print(f"[gate19b:merge-plan] status={plan.status}")
    print("[gate19b:merge-plan] bm25_authoritative=true")
    print("[gate19b:merge-plan] vector_retrieval_authoritative=false")
    print("[gate19b:merge-plan] hybrid_merge_enabled=false")
    print("[gate19b:merge-plan] merge_output_mode=disabled_plan_only")


if __name__ == "__main__":
    main()
