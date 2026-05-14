from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from app.scripts.actual_corpus_search_context_dry_run import build_actual_corpus_search_context_dry_run_report
from app.scripts.extract_kb_source_manifest import repo_root


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _repo_tempdir() -> TemporaryDirectory[str]:
    return TemporaryDirectory(dir=repo_root())


def test_not_ready_when_prerequisites_missing() -> None:
    with _repo_tempdir() as tmp:
        root = Path(tmp)
        report = build_actual_corpus_search_context_dry_run_report(
            source_inventory=root / "source_inventory.json",
            portfolio_extraction=root / "portfolio_extraction.json",
            kb_fix_rows=root / "kb_fix_rows.json",
            evidence_map=root / "kb_evidence_map.json",
            search_context_output_root=root / "search_context",
            search_context_manifest=root / "kb_search_context_manifest.json",
        )
        _assert(report.status == "ACTUAL_CORPUS_SEARCH_CONTEXT_EXTRACTION_NOT_READY", report.status)
        _assert(report.ready_for_search_context_extraction is False, "should not be ready")
        _assert(len(report.missing_prerequisites) == 4, report.missing_prerequisites)


def test_ready_when_prerequisites_exist() -> None:
    with _repo_tempdir() as tmp:
        root = Path(tmp)
        source_inventory = root / "source_inventory.json"
        portfolio_extraction = root / "portfolio_extraction.json"
        kb_fix_rows = root / "kb_fix_rows.json"
        evidence_map = root / "kb_evidence_map.json"
        for path in (source_inventory, portfolio_extraction, kb_fix_rows, evidence_map):
            path.write_text("{}\n", encoding="utf-8")
        report = build_actual_corpus_search_context_dry_run_report(
            source_inventory=source_inventory,
            portfolio_extraction=portfolio_extraction,
            kb_fix_rows=kb_fix_rows,
            evidence_map=evidence_map,
            search_context_output_root=root / "search_context",
            search_context_manifest=root / "kb_search_context_manifest.json",
        )
        _assert(report.status == "ACTUAL_CORPUS_SEARCH_CONTEXT_EXTRACTION_READY", report.status)
        _assert(report.ready_for_search_context_extraction is True, "should be ready")
        _assert(report.missing_prerequisites == [], report.missing_prerequisites)
        _assert(all(item.exists for item in report.prerequisites), "all prerequisites should exist")


def run_validation() -> None:
    test_not_ready_when_prerequisites_missing()
    test_ready_when_prerequisites_exist()
    print("[gate21f:search-context-dry-run] OK")
    print("[gate21f:search-context-dry-run] missing_prerequisites=not_ready")
    print("[gate21f:search-context-dry-run] all_prerequisites=ready")


if __name__ == "__main__":
    run_validation()
