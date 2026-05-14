from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_ACTUAL_CORPUS_SOURCE_INVENTORY = "kbs/manifests/actual_corpus_source_inventory.json"
DEFAULT_PORTFOLIO_EXTRACTION = "kbs/manifests/portfolio_extraction.json"
DEFAULT_KB_FIX_ROWS = "kbs/manifests/kb_fix_rows.json"
DEFAULT_KB_EVIDENCE_MAP = "kbs/manifests/kb_evidence_map.json"
DEFAULT_SEARCH_CONTEXT_OUTPUT_ROOT = "kbs/search_context"
DEFAULT_SEARCH_CONTEXT_MANIFEST = "kbs/manifests/kb_search_context_manifest.json"
DEFAULT_SEARCH_CONTEXT_DRY_RUN_REPORT = "kbs/retrieval/kb_actual_corpus_search_context_dry_run.v1.json"


@dataclass(frozen=True)
class SearchContextPrerequisite:
    name: str
    path: str
    exists: bool
    required_for: str


@dataclass(frozen=True)
class ActualCorpusSearchContextDryRunReport:
    report_version: str
    status: str
    prerequisites: list[SearchContextPrerequisite]
    ready_for_search_context_extraction: bool
    expected_search_context_output_root: str
    expected_search_context_manifest: str
    missing_prerequisites: list[str] = field(default_factory=list)
    recommended_next_steps: list[str] = field(default_factory=list)


def _relative(path: Path) -> str:
    root = repo_root()
    return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)


def _prerequisite(name: str, path: Path, required_for: str) -> SearchContextPrerequisite:
    return SearchContextPrerequisite(
        name=name,
        path=_relative(path),
        exists=path.exists(),
        required_for=required_for,
    )


def build_actual_corpus_search_context_dry_run_report(
    *,
    source_inventory: Path,
    portfolio_extraction: Path,
    kb_fix_rows: Path,
    evidence_map: Path,
    search_context_output_root: Path,
    search_context_manifest: Path,
) -> ActualCorpusSearchContextDryRunReport:
    prerequisites = [
        _prerequisite("actual_corpus_source_inventory", source_inventory, "portfolio extraction and fix-row extraction"),
        _prerequisite("portfolio_extraction", portfolio_extraction, "evidence map construction"),
        _prerequisite("kb_fix_rows", kb_fix_rows, "evidence map construction"),
        _prerequisite("kb_evidence_map", evidence_map, "search-context extraction"),
    ]
    missing = [item.name for item in prerequisites if not item.exists]
    ready = not missing

    if ready:
        status = "ACTUAL_CORPUS_SEARCH_CONTEXT_EXTRACTION_READY"
        next_steps = [
            "Run search-context extraction using the existing extractor against the evidence map.",
            "Review extraction failures, empty text counts, image-bearing artifacts, and highlight-bearing artifacts before customer demo.",
        ]
    else:
        status = "ACTUAL_CORPUS_SEARCH_CONTEXT_EXTRACTION_NOT_READY"
        next_steps = [
            "Generate missing prerequisites before running search-context extraction.",
            "Use the actual corpus source inventory from Gate 21E as the root input for downstream extraction steps.",
        ]

    return ActualCorpusSearchContextDryRunReport(
        report_version="1",
        status=status,
        prerequisites=prerequisites,
        ready_for_search_context_extraction=ready,
        expected_search_context_output_root=_relative(search_context_output_root),
        expected_search_context_manifest=_relative(search_context_manifest),
        missing_prerequisites=missing,
        recommended_next_steps=next_steps,
    )


def write_search_context_dry_run_report(path: Path, report: ActualCorpusSearchContextDryRunReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Dry-run actual corpus search-context extraction prerequisites.")
    parser.add_argument("--source-inventory", type=Path, default=root / DEFAULT_ACTUAL_CORPUS_SOURCE_INVENTORY)
    parser.add_argument("--portfolio-extraction", type=Path, default=root / DEFAULT_PORTFOLIO_EXTRACTION)
    parser.add_argument("--kb-fix-rows", type=Path, default=root / DEFAULT_KB_FIX_ROWS)
    parser.add_argument("--evidence-map", type=Path, default=root / DEFAULT_KB_EVIDENCE_MAP)
    parser.add_argument("--search-context-output-root", type=Path, default=root / DEFAULT_SEARCH_CONTEXT_OUTPUT_ROOT)
    parser.add_argument("--search-context-manifest", type=Path, default=root / DEFAULT_SEARCH_CONTEXT_MANIFEST)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_SEARCH_CONTEXT_DRY_RUN_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_actual_corpus_search_context_dry_run_report(
        source_inventory=args.source_inventory,
        portfolio_extraction=args.portfolio_extraction,
        kb_fix_rows=args.kb_fix_rows,
        evidence_map=args.evidence_map,
        search_context_output_root=args.search_context_output_root,
        search_context_manifest=args.search_context_manifest,
    )
    write_search_context_dry_run_report(args.output, report)
    print(f"[gate21f:search-context-dry-run] Wrote dry-run report: {args.output}")
    print(f"[gate21f:search-context-dry-run] status={report.status}")
    print(f"[gate21f:search-context-dry-run] ready_for_search_context_extraction={'true' if report.ready_for_search_context_extraction else 'false'}")
    for prerequisite in report.prerequisites:
        print(
            "[gate21f:search-context-dry-run] "
            f"{prerequisite.name}={'present' if prerequisite.exists else 'missing'} "
            f"path={prerequisite.path}"
        )
    print(f"[gate21f:search-context-dry-run] missing_prerequisite_count={len(report.missing_prerequisites)}")


if __name__ == "__main__":
    main()
