from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.hybrid_retrieval_score_normalization_design import (
    DEFAULT_SCORE_NORMALIZATION_DESIGN,
    build_score_normalization_design,
    write_score_normalization_design,
)


DEFAULT_CITATION_PRESERVATION_REPORT = "kbs/retrieval/kb_hybrid_retrieval_citation_preservation.v1.json"

REQUIRED_TRACE_FIELDS = [
    "source_artifact_path",
    "kb_document_id",
    "bug_patch_number",
    "child_sha256",
]


@dataclass(frozen=True)
class HybridCitationCandidate:
    candidate_id: str
    source_mode: str
    rank: int
    chunk_id: str
    citation_payload: dict[str, Any]
    bm25_score: float | None = None
    vector_score: float | None = None
    normalized_score: float | None = None


@dataclass(frozen=True)
class HybridCitationPreservationReport:
    report_version: str
    status: str
    source_score_normalization_design: str
    candidate_count: int
    missing_citation_count: int
    missing_trace_field_count: int
    checked_candidates: list[HybridCitationCandidate] = field(default_factory=list)
    required_trace_fields: list[str] = field(default_factory=lambda: REQUIRED_TRACE_FIELDS.copy())
    citation_preservation_required: bool = True
    hybrid_merge_enabled: bool = False
    merged_results_written: bool = False
    production_semantic_retrieval_enabled: bool = False


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def ensure_score_design(path: Path) -> None:
    if path.exists():
        return
    root = repo_root()
    merge_plan = root / "kbs" / "retrieval" / "kb_hybrid_retrieval_fixture_merge_plan.v1.json"
    design = build_score_normalization_design(fixture_merge_plan_path=merge_plan)
    write_score_normalization_design(path, design)


def fixture_candidates() -> list[HybridCitationCandidate]:
    citation_payloads = [
        {
            "source_artifact_path": "kbs/source_artifacts/KB881136.md",
            "kb_document_id": "KB881136",
            "bug_patch_number": "39007114",
            "child_sha256": "fixture-child-sha256-001",
        },
        {
            "source_artifact_path": "kbs/source_artifacts/KB881136.md",
            "kb_document_id": "KB881136",
            "bug_patch_number": "38966530",
            "child_sha256": "fixture-child-sha256-002",
        },
        {
            "source_artifact_path": "kbs/source_artifacts/KB881135.md",
            "kb_document_id": "KB881135",
            "bug_patch_number": "39127058",
            "child_sha256": "fixture-child-sha256-003",
        },
    ]
    return [
        HybridCitationCandidate(
            candidate_id=f"hybrid-candidate-{index:04d}",
            source_mode="fixture_validation",
            rank=index,
            chunk_id=f"fixture-chunk-{index:04d}",
            citation_payload=payload,
            bm25_score=None,
            vector_score=None,
            normalized_score=None,
        )
        for index, payload in enumerate(citation_payloads, start=1)
    ]


def validate_candidate_citations(candidates: list[HybridCitationCandidate]) -> tuple[int, int]:
    missing_citation_count = 0
    missing_trace_field_count = 0
    for candidate in candidates:
        if not candidate.citation_payload:
            missing_citation_count += 1
            missing_trace_field_count += len(REQUIRED_TRACE_FIELDS)
            continue
        for field_name in REQUIRED_TRACE_FIELDS:
            if not str(candidate.citation_payload.get(field_name) or ""):
                missing_trace_field_count += 1
    return missing_citation_count, missing_trace_field_count


def build_citation_preservation_report(*, score_design_path: Path) -> HybridCitationPreservationReport:
    ensure_score_design(score_design_path)
    design = read_json(score_design_path)
    if design.get("status") != "HYBRID_SCORE_NORMALIZATION_DESIGN_READY":
        raise ValueError(f"Score normalization design is not ready: {design.get('status')}")
    if design.get("hybrid_merge_enabled") is not False:
        raise ValueError("Citation preservation validator requires hybrid_merge_enabled=false")
    if design.get("merged_results_written") is not False:
        raise ValueError("Citation preservation validator requires merged_results_written=false")
    candidates = fixture_candidates()
    missing_citation_count, missing_trace_field_count = validate_candidate_citations(candidates)
    root = repo_root()
    return HybridCitationPreservationReport(
        report_version="1",
        status="HYBRID_CITATION_PRESERVATION_VALID" if missing_citation_count == 0 and missing_trace_field_count == 0 else "HYBRID_CITATION_PRESERVATION_INVALID",
        source_score_normalization_design=str(score_design_path.relative_to(root)) if score_design_path.is_relative_to(root) else str(score_design_path),
        candidate_count=len(candidates),
        missing_citation_count=missing_citation_count,
        missing_trace_field_count=missing_trace_field_count,
        checked_candidates=candidates,
        citation_preservation_required=True,
        hybrid_merge_enabled=False,
        merged_results_written=False,
        production_semantic_retrieval_enabled=False,
    )


def write_citation_preservation_report(path: Path, report: HybridCitationPreservationReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate hybrid retrieval citation preservation contract.")
    parser.add_argument("--score-design", type=Path, default=root / DEFAULT_SCORE_NORMALIZATION_DESIGN)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_CITATION_PRESERVATION_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_citation_preservation_report(score_design_path=args.score_design)
    write_citation_preservation_report(args.output, report)
    print(f"[gate19d:citation] Wrote citation preservation report: {args.output}")
    print(f"[gate19d:citation] status={report.status}")
    print(f"[gate19d:citation] candidate_count={report.candidate_count}")
    print(f"[gate19d:citation] missing_citation_count={report.missing_citation_count}")
    print(f"[gate19d:citation] missing_trace_field_count={report.missing_trace_field_count}")
    print("[gate19d:citation] merged_results_written=false")


if __name__ == "__main__":
    main()
