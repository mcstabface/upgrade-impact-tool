from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.hybrid_retrieval_citation_preservation_validator import (
    DEFAULT_CITATION_PRESERVATION_REPORT,
    build_citation_preservation_report,
    write_citation_preservation_report,
)


DEFAULT_ENABLEMENT_REPORT = "kbs/retrieval/kb_production_semantic_retrieval_enablement_gate.v1.json"


@dataclass(frozen=True)
class EnablementCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class ProductionSemanticRetrievalEnablementReport:
    report_version: str
    status: str
    source_citation_preservation_report: str
    checks: list[EnablementCheck]
    passed_count: int
    failed_count: int
    blockers: list[str] = field(default_factory=list)
    explicit_enablement_requested: bool = False
    operator_approval_recorded: bool = False
    production_semantic_retrieval_enabled: bool = False
    hybrid_merge_enabled: bool = False
    merged_results_written: bool = False
    vector_retrieval_authoritative: bool = False
    bm25_authoritative: bool = True
    fail_closed: bool = True


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def ensure_citation_preservation_report(path: Path) -> None:
    if path.exists():
        return
    root = repo_root()
    score_design = root / "kbs" / "retrieval" / "kb_hybrid_retrieval_score_normalization_design.v1.json"
    report = build_citation_preservation_report(score_design_path=score_design)
    write_citation_preservation_report(path, report)


def build_enablement_gate_report(*, citation_preservation_path: Path, explicit_enablement_requested: bool = False, operator_approval_recorded: bool = False) -> ProductionSemanticRetrievalEnablementReport:
    ensure_citation_preservation_report(citation_preservation_path)
    citation_report = read_json(citation_preservation_path)
    checks: list[EnablementCheck] = []
    blockers: list[str] = []

    def add_check(name: str, passed: bool, detail: str) -> None:
        checks.append(EnablementCheck(name=name, passed=passed, detail=detail))
        if not passed:
            blockers.append(name)

    add_check(
        "citation_preservation_valid",
        citation_report.get("status") == "HYBRID_CITATION_PRESERVATION_VALID",
        f"status={citation_report.get('status')}",
    )
    add_check(
        "citation_trace_complete",
        int(citation_report.get("missing_citation_count") or 0) == 0 and int(citation_report.get("missing_trace_field_count") or 0) == 0,
        f"missing_citation_count={citation_report.get('missing_citation_count')} missing_trace_field_count={citation_report.get('missing_trace_field_count')}",
    )
    add_check(
        "upstream_hybrid_merge_disabled",
        citation_report.get("hybrid_merge_enabled") is False,
        f"hybrid_merge_enabled={citation_report.get('hybrid_merge_enabled')}",
    )
    add_check(
        "upstream_merged_results_absent",
        citation_report.get("merged_results_written") is False,
        f"merged_results_written={citation_report.get('merged_results_written')}",
    )
    add_check(
        "explicit_enablement_not_requested",
        explicit_enablement_requested is False,
        f"explicit_enablement_requested={explicit_enablement_requested}",
    )
    add_check(
        "operator_approval_absent",
        operator_approval_recorded is False,
        f"operator_approval_recorded={operator_approval_recorded}",
    )

    failed_count = sum(1 for check in checks if not check.passed)
    passed_count = len(checks) - failed_count
    root = repo_root()
    return ProductionSemanticRetrievalEnablementReport(
        report_version="1",
        status="PRODUCTION_SEMANTIC_RETRIEVAL_DISABLED" if failed_count == 0 else "PRODUCTION_SEMANTIC_RETRIEVAL_ENABLEMENT_BLOCKED",
        source_citation_preservation_report=str(citation_preservation_path.relative_to(root)) if citation_preservation_path.is_relative_to(root) else str(citation_preservation_path),
        checks=checks,
        passed_count=passed_count,
        failed_count=failed_count,
        blockers=blockers,
        explicit_enablement_requested=explicit_enablement_requested,
        operator_approval_recorded=operator_approval_recorded,
        production_semantic_retrieval_enabled=False,
        hybrid_merge_enabled=False,
        merged_results_written=False,
        vector_retrieval_authoritative=False,
        bm25_authoritative=True,
        fail_closed=True,
    )


def write_enablement_gate_report(path: Path, report: ProductionSemanticRetrievalEnablementReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build production semantic retrieval enablement gate report.")
    parser.add_argument("--citation-preservation", type=Path, default=root / DEFAULT_CITATION_PRESERVATION_REPORT)
    parser.add_argument("--explicit-enable", action="store_true")
    parser.add_argument("--operator-approved", action="store_true")
    parser.add_argument("--output", type=Path, default=root / DEFAULT_ENABLEMENT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_enablement_gate_report(
        citation_preservation_path=args.citation_preservation,
        explicit_enablement_requested=args.explicit_enable,
        operator_approval_recorded=args.operator_approved,
    )
    write_enablement_gate_report(args.output, report)
    print(f"[gate19e:enablement] Wrote production semantic retrieval enablement report: {args.output}")
    print(f"[gate19e:enablement] status={report.status}")
    print(f"[gate19e:enablement] passed_checks={report.passed_count}")
    print(f"[gate19e:enablement] failed_checks={report.failed_count}")
    print("[gate19e:enablement] production_semantic_retrieval_enabled=false")
    print("[gate19e:enablement] fail_closed=true")


if __name__ == "__main__":
    main()
