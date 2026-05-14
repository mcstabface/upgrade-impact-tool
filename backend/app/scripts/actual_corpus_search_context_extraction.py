from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.scripts.actual_corpus_prerequisite_regeneration import build_actual_corpus_prerequisite_regeneration_report
from app.scripts.actual_corpus_search_context_dry_run import (
    DEFAULT_ACTUAL_CORPUS_SOURCE_INVENTORY,
    DEFAULT_KB_EVIDENCE_MAP,
    DEFAULT_KB_FIX_ROWS,
    DEFAULT_PORTFOLIO_EXTRACTION,
)
from app.scripts.actual_corpus_source_inventory_extraction import DEFAULT_RAW_CORPUS_ROOT
from app.scripts.extract_kb_search_context import build_manifest, write_manifest
from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_SEARCH_CONTEXT_OUTPUT_ROOT = "kbs/search_context"
DEFAULT_SEARCH_CONTEXT_MANIFEST = "kbs/manifests/kb_search_context_manifest.json"
DEFAULT_SEARCH_CONTEXT_EXTRACTION_REPORT = "kbs/retrieval/kb_actual_corpus_search_context_extraction.v1.json"


@dataclass(frozen=True)
class ActualCorpusSearchContextExtractionReport:
    report_version: str
    status: str
    prerequisite_status: str
    source_inventory_status: str
    readiness_status: str
    ready_for_search_context_extraction: bool
    evidence_map_path: str
    output_root: str
    manifest_output: str
    matched_row_count: int
    artifact_count: int
    extraction_failed_count: int
    empty_text_count: int
    image_bearing_artifact_count: int
    highlight_bearing_artifact_count: int
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    recommended_next_steps: list[str] = field(default_factory=list)


def _relative(path: Path) -> str:
    root = repo_root()
    return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)


def build_actual_corpus_search_context_extraction_report(
    *,
    source_root: Path,
    inventory_output: Path,
    portfolio_extraction: Path,
    kb_fix_rows: Path,
    evidence_map: Path,
    output_root: Path,
    manifest_output: Path,
) -> ActualCorpusSearchContextExtractionReport:
    prerequisite_report = build_actual_corpus_prerequisite_regeneration_report(
        source_root=source_root,
        inventory_output=inventory_output,
        portfolio_extraction=portfolio_extraction,
        kb_fix_rows=kb_fix_rows,
        evidence_map=evidence_map,
        search_context_output_root=output_root,
        search_context_manifest=manifest_output,
    )

    errors = list(prerequisite_report.errors)
    if not prerequisite_report.ready_for_search_context_extraction:
        return ActualCorpusSearchContextExtractionReport(
            report_version="1",
            status="ACTUAL_CORPUS_SEARCH_CONTEXT_EXTRACTION_BLOCKED",
            prerequisite_status=prerequisite_report.status,
            source_inventory_status=prerequisite_report.source_inventory_status,
            readiness_status=prerequisite_report.search_context_readiness_status,
            ready_for_search_context_extraction=False,
            evidence_map_path=_relative(evidence_map),
            output_root=_relative(output_root),
            manifest_output=_relative(manifest_output),
            matched_row_count=0,
            artifact_count=0,
            extraction_failed_count=0,
            empty_text_count=0,
            image_bearing_artifact_count=0,
            highlight_bearing_artifact_count=0,
            errors=errors or ["Search-context extraction prerequisites are not ready."],
            recommended_next_steps=["Resolve prerequisite blockers and rerun Gate 21H."],
        )

    output_root.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(evidence_map, output_root)
    write_manifest(manifest, manifest_output)

    if manifest.extraction_failed_count:
        errors.append("One or more search-context artifacts failed extraction.")

    status = (
        "ACTUAL_CORPUS_SEARCH_CONTEXT_EXTRACTED"
        if not errors
        else "ACTUAL_CORPUS_SEARCH_CONTEXT_EXTRACTED_WITH_FAILURES"
    )
    next_steps = [
        "Review generated search-context manifest for empty text, image-bearing pages, and highlight annotations.",
        "Prepare demo query candidates against generated search-context artifacts.",
    ]

    return ActualCorpusSearchContextExtractionReport(
        report_version="1",
        status=status,
        prerequisite_status=prerequisite_report.status,
        source_inventory_status=prerequisite_report.source_inventory_status,
        readiness_status=prerequisite_report.search_context_readiness_status,
        ready_for_search_context_extraction=True,
        evidence_map_path=manifest.evidence_map_path,
        output_root=manifest.output_root,
        manifest_output=_relative(manifest_output),
        matched_row_count=manifest.matched_row_count,
        artifact_count=manifest.artifact_count,
        extraction_failed_count=manifest.extraction_failed_count,
        empty_text_count=manifest.empty_text_count,
        image_bearing_artifact_count=manifest.image_bearing_artifact_count,
        highlight_bearing_artifact_count=manifest.highlight_bearing_artifact_count,
        warnings=list(manifest.warnings),
        errors=errors,
        recommended_next_steps=next_steps,
    )


def write_extraction_report(path: Path, report: ActualCorpusSearchContextExtractionReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Execute actual corpus search-context extraction.")
    parser.add_argument("--source-root", type=Path, default=root / DEFAULT_RAW_CORPUS_ROOT)
    parser.add_argument("--inventory-output", type=Path, default=root / DEFAULT_ACTUAL_CORPUS_SOURCE_INVENTORY)
    parser.add_argument("--portfolio-extraction", type=Path, default=root / DEFAULT_PORTFOLIO_EXTRACTION)
    parser.add_argument("--kb-fix-rows", type=Path, default=root / DEFAULT_KB_FIX_ROWS)
    parser.add_argument("--evidence-map", type=Path, default=root / DEFAULT_KB_EVIDENCE_MAP)
    parser.add_argument("--output-root", type=Path, default=root / DEFAULT_SEARCH_CONTEXT_OUTPUT_ROOT)
    parser.add_argument("--manifest-output", type=Path, default=root / DEFAULT_SEARCH_CONTEXT_MANIFEST)
    parser.add_argument("--report-output", type=Path, default=root / DEFAULT_SEARCH_CONTEXT_EXTRACTION_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_actual_corpus_search_context_extraction_report(
        source_root=args.source_root,
        inventory_output=args.inventory_output,
        portfolio_extraction=args.portfolio_extraction,
        kb_fix_rows=args.kb_fix_rows,
        evidence_map=args.evidence_map,
        output_root=args.output_root,
        manifest_output=args.manifest_output,
    )
    write_extraction_report(args.report_output, report)
    print(f"[gate21h:search-context] Wrote extraction report: {args.report_output}")
    print(f"[gate21h:search-context] status={report.status}")
    print(f"[gate21h:search-context] prerequisite_status={report.prerequisite_status}")
    print(f"[gate21h:search-context] readiness_status={report.readiness_status}")
    print(f"[gate21h:search-context] ready_for_search_context_extraction={'true' if report.ready_for_search_context_extraction else 'false'}")
    print(f"[gate21h:search-context] evidence_map_path={report.evidence_map_path}")
    print(f"[gate21h:search-context] output_root={report.output_root}")
    print(f"[gate21h:search-context] manifest_output={report.manifest_output}")
    print(f"[gate21h:search-context] matched_row_count={report.matched_row_count}")
    print(f"[gate21h:search-context] artifact_count={report.artifact_count}")
    print(f"[gate21h:search-context] extraction_failed_count={report.extraction_failed_count}")
    print(f"[gate21h:search-context] empty_text_count={report.empty_text_count}")
    print(f"[gate21h:search-context] image_bearing_artifact_count={report.image_bearing_artifact_count}")
    print(f"[gate21h:search-context] highlight_bearing_artifact_count={report.highlight_bearing_artifact_count}")


if __name__ == "__main__":
    main()
