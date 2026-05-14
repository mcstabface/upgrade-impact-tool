from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_HYBRID_RETRIEVAL_CONTRACT = "kbs/retrieval/kb_hybrid_retrieval_design_contract.v1.json"


@dataclass(frozen=True)
class HybridRetrievalDesignCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class HybridRetrievalDesignContract:
    report_version: str
    status: str
    bm25_authoritative: bool
    vector_retrieval_authoritative: bool
    vector_retrieval_fixture_only: bool
    hybrid_merge_enabled: bool
    production_semantic_retrieval_enabled: bool
    implicit_reranking_enabled: bool
    draft_generation_enabled: bool
    llm_call_allowed: bool
    retrieval_modes: list[str]
    required_future_gates: list[str]
    checks: list[HybridRetrievalDesignCheck] = field(default_factory=list)
    passed_count: int = 0
    failed_count: int = 0
    blockers: list[str] = field(default_factory=list)


def build_hybrid_retrieval_design_contract() -> HybridRetrievalDesignContract:
    checks: list[HybridRetrievalDesignCheck] = []
    blockers: list[str] = []

    def add_check(name: str, passed: bool, detail: str) -> None:
        checks.append(HybridRetrievalDesignCheck(name=name, passed=passed, detail=detail))
        if not passed:
            blockers.append(name)

    bm25_authoritative = True
    vector_retrieval_authoritative = False
    vector_retrieval_fixture_only = True
    hybrid_merge_enabled = False
    production_semantic_retrieval_enabled = False
    implicit_reranking_enabled = False
    draft_generation_enabled = False
    llm_call_allowed = False
    retrieval_modes = ["bm25_authoritative", "vector_fixture_diagnostic"]
    required_future_gates = [
        "Gate 19B — Hybrid Retrieval Fixture Merge Plan",
        "Gate 19C — Hybrid Retrieval Score Normalization Design",
        "Gate 19D — Hybrid Retrieval Citation Preservation Validator",
        "Gate 19E — Production Semantic Retrieval Enablement Gate",
    ]

    add_check("bm25_remains_authoritative", bm25_authoritative is True, "BM25 remains the only authoritative retrieval path.")
    add_check("vector_retrieval_not_authoritative", vector_retrieval_authoritative is False, "Vector retrieval is not authoritative.")
    add_check("vector_retrieval_fixture_only", vector_retrieval_fixture_only is True, "Vector retrieval remains fixture/diagnostic only.")
    add_check("hybrid_merge_disabled", hybrid_merge_enabled is False, "Hybrid merge is not enabled in Gate 19A.")
    add_check("production_semantic_retrieval_disabled", production_semantic_retrieval_enabled is False, "Production semantic retrieval remains disabled.")
    add_check("implicit_reranking_disabled", implicit_reranking_enabled is False, "No implicit reranking is enabled.")
    add_check("draft_generation_disabled", draft_generation_enabled is False, "Draft generation remains disabled.")
    add_check("llm_calls_disallowed", llm_call_allowed is False, "No LLM calls are allowed by this contract.")

    failed_count = sum(1 for check in checks if not check.passed)
    passed_count = len(checks) - failed_count
    return HybridRetrievalDesignContract(
        report_version="1",
        status="HYBRID_RETRIEVAL_DESIGN_CONTRACT_READY" if failed_count == 0 else "HYBRID_RETRIEVAL_DESIGN_CONTRACT_BLOCKED",
        bm25_authoritative=bm25_authoritative,
        vector_retrieval_authoritative=vector_retrieval_authoritative,
        vector_retrieval_fixture_only=vector_retrieval_fixture_only,
        hybrid_merge_enabled=hybrid_merge_enabled,
        production_semantic_retrieval_enabled=production_semantic_retrieval_enabled,
        implicit_reranking_enabled=implicit_reranking_enabled,
        draft_generation_enabled=draft_generation_enabled,
        llm_call_allowed=llm_call_allowed,
        retrieval_modes=retrieval_modes,
        required_future_gates=required_future_gates,
        checks=checks,
        passed_count=passed_count,
        failed_count=failed_count,
        blockers=blockers,
    )


def write_hybrid_retrieval_design_contract(path: Path, contract: HybridRetrievalDesignContract) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(contract), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build Gate 19A hybrid retrieval design contract.")
    parser.add_argument("--output", type=Path, default=root / DEFAULT_HYBRID_RETRIEVAL_CONTRACT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    contract = build_hybrid_retrieval_design_contract()
    write_hybrid_retrieval_design_contract(args.output, contract)
    print(f"[gate19a:hybrid-design] Wrote hybrid retrieval design contract: {args.output}")
    print(f"[gate19a:hybrid-design] status={contract.status}")
    print(f"[gate19a:hybrid-design] passed_checks={contract.passed_count}")
    print(f"[gate19a:hybrid-design] failed_checks={contract.failed_count}")
    print("[gate19a:hybrid-design] bm25_authoritative=true")
    print("[gate19a:hybrid-design] hybrid_merge_enabled=false")
    print("[gate19a:hybrid-design] production_semantic_retrieval_enabled=false")


if __name__ == "__main__":
    main()
