from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.actual_corpus_search_context_extraction import (
    DEFAULT_SEARCH_CONTEXT_MANIFEST,
    build_actual_corpus_search_context_extraction_report,
)
from app.scripts.actual_corpus_prerequisite_regeneration import DEFAULT_PREREQUISITE_REGENERATION_REPORT
from app.scripts.actual_corpus_search_context_dry_run import (
    DEFAULT_ACTUAL_CORPUS_SOURCE_INVENTORY,
    DEFAULT_KB_EVIDENCE_MAP,
    DEFAULT_KB_FIX_ROWS,
    DEFAULT_PORTFOLIO_EXTRACTION,
)
from app.scripts.actual_corpus_source_inventory_extraction import DEFAULT_RAW_CORPUS_ROOT
from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_SEARCH_CONTEXT_OUTPUT_ROOT = "kbs/search_context"
DEFAULT_SEARCH_CONTEXT_EXTRACTION_REPORT = "kbs/retrieval/kb_actual_corpus_search_context_extraction.v1.json"
DEFAULT_SEARCH_CONTEXT_SUMMARY_REPORT = "kbs/retrieval/kb_actual_corpus_search_context_summary.v1.json"


@dataclass(frozen=True)
class DemoCandidate:
    kb_document_id: str | None
    bug_patch_number: str | None
    product: str | None
    category: str | None
    artifact_path: str
    char_count: int
    page_count: int
    has_images: bool
    has_highlight_annotations: bool


@dataclass(frozen=True)
class ActualCorpusSearchContextSummaryReport:
    report_version: str
    status: str
    extraction_status: str
    manifest_path: str
    output_root: str
    matched_row_count: int
    artifact_count: int
    extraction_failed_count: int
    empty_text_count: int
    image_bearing_artifact_count: int
    highlight_bearing_artifact_count: int
    total_char_count: int
    total_page_count: int
    average_char_count: float
    demo_candidate_count: int
    demo_candidates: list[DemoCandidate]
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    recommended_next_steps: list[str] = field(default_factory=list)


def _relative(path: Path) -> str:
    root = repo_root()
    return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _candidate_from_artifact_record(record: dict[str, Any]) -> DemoCandidate:
    return DemoCandidate(
        kb_document_id=record.get("kb_document_id"),
        bug_patch_number=record.get("bug_patch_number"),
        product=record.get("product"),
        category=record.get("category"),
        artifact_path=record.get("artifact_path") or "",
        char_count=int(record.get("char_count") or 0),
        page_count=int(record.get("page_count") or 0),
        has_images=bool(record.get("has_images")),
        has_highlight_annotations=bool(record.get("has_highlight_annotations")),
    )


def build_summary_from_manifest(*, manifest_path: Path, extraction_status: str) -> ActualCorpusSearchContextSummaryReport:
    if not manifest_path.exists():
        return ActualCorpusSearchContextSummaryReport(
            report_version="1",
            status="ACTUAL_CORPUS_SEARCH_CONTEXT_SUMMARY_BLOCKED",
            extraction_status=extraction_status,
            manifest_path=_relative(manifest_path),
            output_root="",
            matched_row_count=0,
            artifact_count=0,
            extraction_failed_count=0,
            empty_text_count=0,
            image_bearing_artifact_count=0,
            highlight_bearing_artifact_count=0,
            total_char_count=0,
            total_page_count=0,
            average_char_count=0.0,
            demo_candidate_count=0,
            demo_candidates=[],
            errors=[f"search-context manifest not found: {manifest_path}"],
            recommended_next_steps=["Run actual corpus search-context extraction before summary generation."],
        )

    manifest = _read_json(manifest_path)
    artifacts = list(manifest.get("artifacts") or [])
    total_char_count = sum(int(record.get("char_count") or 0) for record in artifacts)
    total_page_count = sum(int(record.get("page_count") or 0) for record in artifacts)
    artifact_count = int(manifest.get("artifact_count") or len(artifacts))
    average_char_count = round(total_char_count / artifact_count, 2) if artifact_count else 0.0

    demo_candidates = [
        _candidate_from_artifact_record(record)
        for record in sorted(
            artifacts,
            key=lambda item: (
                int(item.get("char_count") or 0),
                str(item.get("kb_document_id") or ""),
                str(item.get("bug_patch_number") or ""),
            ),
            reverse=True,
        )[:10]
    ]

    extraction_failed_count = int(manifest.get("extraction_failed_count") or 0)
    empty_text_count = int(manifest.get("empty_text_count") or 0)
    errors: list[str] = []
    if extraction_failed_count:
        errors.append("One or more search-context artifacts failed extraction.")
    if empty_text_count:
        errors.append("One or more search-context artifacts contain no text.")

    status = (
        "ACTUAL_CORPUS_SEARCH_CONTEXT_SUMMARY_READY"
        if not errors
        else "ACTUAL_CORPUS_SEARCH_CONTEXT_SUMMARY_READY_WITH_WARNINGS"
    )

    return ActualCorpusSearchContextSummaryReport(
        report_version="1",
        status=status,
        extraction_status=extraction_status,
        manifest_path=_relative(manifest_path),
        output_root=str(manifest.get("output_root") or ""),
        matched_row_count=int(manifest.get("matched_row_count") or 0),
        artifact_count=artifact_count,
        extraction_failed_count=extraction_failed_count,
        empty_text_count=empty_text_count,
        image_bearing_artifact_count=int(manifest.get("image_bearing_artifact_count") or 0),
        highlight_bearing_artifact_count=int(manifest.get("highlight_bearing_artifact_count") or 0),
        total_char_count=total_char_count,
        total_page_count=total_page_count,
        average_char_count=average_char_count,
        demo_candidate_count=len(demo_candidates),
        demo_candidates=demo_candidates,
        warnings=list(manifest.get("warnings") or []),
        errors=errors,
        recommended_next_steps=[
            "Review the top demo candidates for customer-relevant query themes.",
            "Capture 5-10 customer questions before tuning retrieval behavior.",
            "Use the generated search-context artifacts as the evidence base for the customer demo.",
        ],
    )


def build_actual_corpus_search_context_summary_report(
    *,
    source_root: Path,
    inventory_output: Path,
    portfolio_extraction: Path,
    kb_fix_rows: Path,
    evidence_map: Path,
    output_root: Path,
    manifest_output: Path,
) -> ActualCorpusSearchContextSummaryReport:
    extraction_report = build_actual_corpus_search_context_extraction_report(
        source_root=source_root,
        inventory_output=inventory_output,
        portfolio_extraction=portfolio_extraction,
        kb_fix_rows=kb_fix_rows,
        evidence_map=evidence_map,
        output_root=output_root,
        manifest_output=manifest_output,
    )
    return build_summary_from_manifest(
        manifest_path=manifest_output,
        extraction_status=extraction_report.status,
    )


def write_summary_report(path: Path, report: ActualCorpusSearchContextSummaryReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Generate actual corpus search-context summary for demo readiness.")
    parser.add_argument("--source-root", type=Path, default=root / DEFAULT_RAW_CORPUS_ROOT)
    parser.add_argument("--inventory-output", type=Path, default=root / DEFAULT_ACTUAL_CORPUS_SOURCE_INVENTORY)
    parser.add_argument("--portfolio-extraction", type=Path, default=root / DEFAULT_PORTFOLIO_EXTRACTION)
    parser.add_argument("--kb-fix-rows", type=Path, default=root / DEFAULT_KB_FIX_ROWS)
    parser.add_argument("--evidence-map", type=Path, default=root / DEFAULT_KB_EVIDENCE_MAP)
    parser.add_argument("--output-root", type=Path, default=root / DEFAULT_SEARCH_CONTEXT_OUTPUT_ROOT)
    parser.add_argument("--manifest-output", type=Path, default=root / DEFAULT_SEARCH_CONTEXT_MANIFEST)
    parser.add_argument("--summary-output", type=Path, default=root / DEFAULT_SEARCH_CONTEXT_SUMMARY_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_actual_corpus_search_context_summary_report(
        source_root=args.source_root,
        inventory_output=args.inventory_output,
        portfolio_extraction=args.portfolio_extraction,
        kb_fix_rows=args.kb_fix_rows,
        evidence_map=args.evidence_map,
        output_root=args.output_root,
        manifest_output=args.manifest_output,
    )
    write_summary_report(args.summary_output, report)
    print(f"[gate21i:search-context-summary] Wrote summary report: {args.summary_output}")
    print(f"[gate21i:search-context-summary] status={report.status}")
    print(f"[gate21i:search-context-summary] extraction_status={report.extraction_status}")
    print(f"[gate21i:search-context-summary] manifest_path={report.manifest_path}")
    print(f"[gate21i:search-context-summary] output_root={report.output_root}")
    print(f"[gate21i:search-context-summary] matched_row_count={report.matched_row_count}")
    print(f"[gate21i:search-context-summary] artifact_count={report.artifact_count}")
    print(f"[gate21i:search-context-summary] extraction_failed_count={report.extraction_failed_count}")
    print(f"[gate21i:search-context-summary] empty_text_count={report.empty_text_count}")
    print(f"[gate21i:search-context-summary] image_bearing_artifact_count={report.image_bearing_artifact_count}")
    print(f"[gate21i:search-context-summary] highlight_bearing_artifact_count={report.highlight_bearing_artifact_count}")
    print(f"[gate21i:search-context-summary] total_char_count={report.total_char_count}")
    print(f"[gate21i:search-context-summary] total_page_count={report.total_page_count}")
    print(f"[gate21i:search-context-summary] demo_candidate_count={report.demo_candidate_count}")


if __name__ == "__main__":
    main()
