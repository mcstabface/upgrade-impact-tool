from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.scripts.actual_corpus_search_context_dry_run import (
    DEFAULT_ACTUAL_CORPUS_SOURCE_INVENTORY,
    DEFAULT_KB_EVIDENCE_MAP,
    DEFAULT_KB_FIX_ROWS,
    DEFAULT_PORTFOLIO_EXTRACTION,
    DEFAULT_SEARCH_CONTEXT_MANIFEST,
    DEFAULT_SEARCH_CONTEXT_OUTPUT_ROOT,
    build_actual_corpus_search_context_dry_run_report,
)
from app.scripts.actual_corpus_source_inventory_extraction import (
    DEFAULT_RAW_CORPUS_ROOT,
    extract_actual_corpus_source_inventory,
)
from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_PREREQUISITE_REGENERATION_REPORT = "kbs/retrieval/kb_actual_corpus_prerequisite_regeneration.v1.json"


@dataclass(frozen=True)
class ActualCorpusPrerequisiteRegenerationReport:
    report_version: str
    status: str
    source_inventory_status: str
    search_context_readiness_status: str
    ready_for_search_context_extraction: bool
    source_root: str
    inventory_manifest_path: str
    html_source_count: int
    portfolio_file_count: int
    kb_document_count: int
    missing_portfolio_count: int
    unreferenced_portfolio_count: int
    missing_prerequisites: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    recommended_next_steps: list[str] = field(default_factory=list)


def build_actual_corpus_prerequisite_regeneration_report(
    *,
    source_root: Path,
    inventory_output: Path,
    portfolio_extraction: Path,
    kb_fix_rows: Path,
    evidence_map: Path,
    search_context_output_root: Path,
    search_context_manifest: Path,
) -> ActualCorpusPrerequisiteRegenerationReport:
    inventory_report = extract_actual_corpus_source_inventory(
        source_root=source_root,
        inventory_output=inventory_output,
    )
    readiness_report = build_actual_corpus_search_context_dry_run_report(
        source_inventory=inventory_output,
        portfolio_extraction=portfolio_extraction,
        kb_fix_rows=kb_fix_rows,
        evidence_map=evidence_map,
        search_context_output_root=search_context_output_root,
        search_context_manifest=search_context_manifest,
    )

    errors = list(inventory_report.errors)
    warnings = list(inventory_report.warnings)
    missing_prerequisites = list(readiness_report.missing_prerequisites)
    if not readiness_report.ready_for_search_context_extraction:
        errors.append("Search-context extraction prerequisites are incomplete after regeneration.")

    if not errors:
        status = "ACTUAL_CORPUS_PREREQUISITES_REGENERATED_READY"
        next_steps = [
            "Run actual corpus search-context extraction using the existing extraction path.",
            "Review generated search-context extraction metrics before customer demo query preparation.",
        ]
    else:
        status = "ACTUAL_CORPUS_PREREQUISITES_REGENERATION_BLOCKED"
        next_steps = [
            "Resolve missing prerequisite artifacts before search-context extraction.",
            "Rerun prerequisite regeneration after correcting the reported blocker.",
        ]

    return ActualCorpusPrerequisiteRegenerationReport(
        report_version="1",
        status=status,
        source_inventory_status=inventory_report.status,
        search_context_readiness_status=readiness_report.status,
        ready_for_search_context_extraction=readiness_report.ready_for_search_context_extraction,
        source_root=inventory_report.source_root,
        inventory_manifest_path=inventory_report.inventory_manifest_path,
        html_source_count=inventory_report.html_source_count,
        portfolio_file_count=inventory_report.portfolio_file_count,
        kb_document_count=inventory_report.kb_document_count,
        missing_portfolio_count=inventory_report.missing_portfolio_count,
        unreferenced_portfolio_count=inventory_report.unreferenced_portfolio_count,
        missing_prerequisites=missing_prerequisites,
        warnings=warnings,
        errors=errors,
        recommended_next_steps=next_steps,
    )


def write_prerequisite_regeneration_report(path: Path, report: ActualCorpusPrerequisiteRegenerationReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Regenerate actual corpus prerequisites and check search-context readiness.")
    parser.add_argument("--source-root", type=Path, default=root / DEFAULT_RAW_CORPUS_ROOT)
    parser.add_argument("--inventory-output", type=Path, default=root / DEFAULT_ACTUAL_CORPUS_SOURCE_INVENTORY)
    parser.add_argument("--portfolio-extraction", type=Path, default=root / DEFAULT_PORTFOLIO_EXTRACTION)
    parser.add_argument("--kb-fix-rows", type=Path, default=root / DEFAULT_KB_FIX_ROWS)
    parser.add_argument("--evidence-map", type=Path, default=root / DEFAULT_KB_EVIDENCE_MAP)
    parser.add_argument("--search-context-output-root", type=Path, default=root / DEFAULT_SEARCH_CONTEXT_OUTPUT_ROOT)
    parser.add_argument("--search-context-manifest", type=Path, default=root / DEFAULT_SEARCH_CONTEXT_MANIFEST)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_PREREQUISITE_REGENERATION_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_actual_corpus_prerequisite_regeneration_report(
        source_root=args.source_root,
        inventory_output=args.inventory_output,
        portfolio_extraction=args.portfolio_extraction,
        kb_fix_rows=args.kb_fix_rows,
        evidence_map=args.evidence_map,
        search_context_output_root=args.search_context_output_root,
        search_context_manifest=args.search_context_manifest,
    )
    write_prerequisite_regeneration_report(args.output, report)
    print(f"[gate21g:prereq-regen] Wrote prerequisite regeneration report: {args.output}")
    print(f"[gate21g:prereq-regen] status={report.status}")
    print(f"[gate21g:prereq-regen] source_inventory_status={report.source_inventory_status}")
    print(f"[gate21g:prereq-regen] search_context_readiness_status={report.search_context_readiness_status}")
    print(f"[gate21g:prereq-regen] ready_for_search_context_extraction={'true' if report.ready_for_search_context_extraction else 'false'}")
    print(f"[gate21g:prereq-regen] inventory_manifest_path={report.inventory_manifest_path}")
    print(f"[gate21g:prereq-regen] html_source_count={report.html_source_count}")
    print(f"[gate21g:prereq-regen] portfolio_file_count={report.portfolio_file_count}")
    print(f"[gate21g:prereq-regen] kb_document_count={report.kb_document_count}")
    print(f"[gate21g:prereq-regen] missing_prerequisite_count={len(report.missing_prerequisites)}")


if __name__ == "__main__":
    main()
