from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.hybrid_retrieval_fixture_merge_plan import (
    DEFAULT_FIXTURE_MERGE_PLAN,
    build_fixture_merge_plan,
    write_fixture_merge_plan,
)


DEFAULT_SCORE_NORMALIZATION_DESIGN = "kbs/retrieval/kb_hybrid_retrieval_score_normalization_design.v1.json"


@dataclass(frozen=True)
class ScoreNormalizationRule:
    name: str
    enabled: bool
    formula: str
    detail: str


@dataclass(frozen=True)
class HybridRetrievalScoreNormalizationDesign:
    report_version: str
    status: str
    source_fixture_merge_plan: str
    score_normalization_enabled: bool
    normalization_design_only: bool
    hybrid_merge_enabled: bool
    reranking_enabled: bool
    production_semantic_retrieval_enabled: bool
    bm25_authoritative: bool
    vector_retrieval_authoritative: bool
    normalized_scores_written: bool
    merged_results_written: bool
    formulas: list[ScoreNormalizationRule] = field(default_factory=list)
    required_future_gates: list[str] = field(default_factory=list)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def ensure_fixture_merge_plan(path: Path) -> None:
    if path.exists():
        return
    write_fixture_merge_plan(path, build_fixture_merge_plan(design_contract_path=repo_root() / "kbs" / "retrieval" / "kb_hybrid_retrieval_design_contract.v1.json"))


def build_score_normalization_design(*, fixture_merge_plan_path: Path) -> HybridRetrievalScoreNormalizationDesign:
    ensure_fixture_merge_plan(fixture_merge_plan_path)
    plan = read_json(fixture_merge_plan_path)
    if plan.get("status") != "HYBRID_RETRIEVAL_FIXTURE_MERGE_PLAN_READY":
        raise ValueError(f"Fixture merge plan is not ready: {plan.get('status')}")
    if plan.get("hybrid_merge_enabled") is not False:
        raise ValueError("Score normalization design requires hybrid_merge_enabled=false")
    if plan.get("bm25_authoritative") is not True:
        raise ValueError("Score normalization design requires bm25_authoritative=true")
    if plan.get("vector_retrieval_authoritative") is not False:
        raise ValueError("Score normalization design requires vector_retrieval_authoritative=false")
    formulas = [
        ScoreNormalizationRule(
            name="bm25_min_max_normalization",
            enabled=False,
            formula="(score - min_bm25_score) / max(max_bm25_score - min_bm25_score, epsilon)",
            detail="Design-only BM25 normalization formula; not executed in Gate 19C.",
        ),
        ScoreNormalizationRule(
            name="vector_cosine_shift_scale",
            enabled=False,
            formula="(cosine_score + 1.0) / 2.0",
            detail="Design-only cosine normalization formula; not executed in Gate 19C.",
        ),
        ScoreNormalizationRule(
            name="weighted_hybrid_score",
            enabled=False,
            formula="(bm25_weight * bm25_normalized) + (vector_weight * vector_normalized)",
            detail="Design-only hybrid score formula; no merged score is emitted in Gate 19C.",
        ),
    ]
    root = repo_root()
    return HybridRetrievalScoreNormalizationDesign(
        report_version="1",
        status="HYBRID_SCORE_NORMALIZATION_DESIGN_READY",
        source_fixture_merge_plan=str(fixture_merge_plan_path.relative_to(root)) if fixture_merge_plan_path.is_relative_to(root) else str(fixture_merge_plan_path),
        score_normalization_enabled=False,
        normalization_design_only=True,
        hybrid_merge_enabled=False,
        reranking_enabled=False,
        production_semantic_retrieval_enabled=False,
        bm25_authoritative=True,
        vector_retrieval_authoritative=False,
        normalized_scores_written=False,
        merged_results_written=False,
        formulas=formulas,
        required_future_gates=[
            "Gate 19D — Hybrid Retrieval Citation Preservation Validator",
            "Gate 19E — Production Semantic Retrieval Enablement Gate",
        ],
    )


def write_score_normalization_design(path: Path, design: HybridRetrievalScoreNormalizationDesign) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(design), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build Gate 19C hybrid retrieval score normalization design.")
    parser.add_argument("--fixture-merge-plan", type=Path, default=root / DEFAULT_FIXTURE_MERGE_PLAN)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_SCORE_NORMALIZATION_DESIGN)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    design = build_score_normalization_design(fixture_merge_plan_path=args.fixture_merge_plan)
    write_score_normalization_design(args.output, design)
    print(f"[gate19c:score-design] Wrote score normalization design: {args.output}")
    print(f"[gate19c:score-design] status={design.status}")
    print("[gate19c:score-design] score_normalization_enabled=false")
    print("[gate19c:score-design] normalized_scores_written=false")
    print("[gate19c:score-design] hybrid_merge_enabled=false")
    print("[gate19c:score-design] merged_results_written=false")


if __name__ == "__main__":
    main()
