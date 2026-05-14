from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.scripts.actual_corpus_search_context_extraction import build_actual_corpus_search_context_extraction_report
from app.scripts.extract_kb_source_manifest import repo_root


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _repo_tempdir() -> TemporaryDirectory[str]:
    return TemporaryDirectory(dir=repo_root())


def _write_source_fixture(source: Path) -> None:
    source.mkdir(parents=True)
    portfolio = source / "CCS_1.0_MP1_PFDs_Portfolio.pdf"
    portfolio.write_bytes(b"%PDF-1.4\n%%EOF\n")
    html = source / "KB12345.html"
    html.write_text(
        """
        <html><body>
        <a href="https://example.test/?documentId=KB12345">KB12345</a>
        Hot Fix Release 1 About Window: CCS_1.0_MP1_PFDs_Portfolio.pdf
        </body></html>
        """,
        encoding="utf-8",
    )


def _write_prerequisites(root: Path) -> tuple[Path, Path, Path]:
    portfolio_extraction = root / "portfolio_extraction.json"
    kb_fix_rows = root / "kb_fix_rows.json"
    evidence_map = root / "kb_evidence_map.json"
    portfolio_extraction.write_text("{}\n", encoding="utf-8")
    kb_fix_rows.write_text("{}\n", encoding="utf-8")
    return portfolio_extraction, kb_fix_rows, evidence_map


def _write_empty_evidence_map(path: Path) -> None:
    path.write_text(json.dumps({"documents": []}, indent=2) + "\n", encoding="utf-8")


def test_extraction_blocked_when_prerequisites_missing() -> None:
    with _repo_tempdir() as tmp:
        root = Path(tmp)
        source = root / "raw"
        _write_source_fixture(source)
        inventory = root / "actual_corpus_source_inventory.json"
        portfolio_extraction = root / "portfolio_extraction.json"
        kb_fix_rows = root / "kb_fix_rows.json"
        evidence_map = root / "kb_evidence_map.json"
        portfolio_extraction.write_text("{}\n", encoding="utf-8")
        kb_fix_rows.write_text("{}\n", encoding="utf-8")
        report = build_actual_corpus_search_context_extraction_report(
            source_root=source,
            inventory_output=inventory,
            portfolio_extraction=portfolio_extraction,
            kb_fix_rows=kb_fix_rows,
            evidence_map=evidence_map,
            output_root=root / "search_context",
            manifest_output=root / "kb_search_context_manifest.json",
        )
        _assert(report.status == "ACTUAL_CORPUS_SEARCH_CONTEXT_EXTRACTION_BLOCKED", report.status)
        _assert(report.ready_for_search_context_extraction is False, "should be blocked")
        _assert(report.artifact_count == 0, str(report.artifact_count))
        _assert(report.errors, "blocked report must include errors")


def test_extraction_runs_with_empty_evidence_map() -> None:
    with _repo_tempdir() as tmp:
        root = Path(tmp)
        source = root / "raw"
        _write_source_fixture(source)
        inventory = root / "actual_corpus_source_inventory.json"
        portfolio_extraction, kb_fix_rows, evidence_map = _write_prerequisites(root)
        _write_empty_evidence_map(evidence_map)
        manifest_output = root / "kb_search_context_manifest.json"
        report = build_actual_corpus_search_context_extraction_report(
            source_root=source,
            inventory_output=inventory,
            portfolio_extraction=portfolio_extraction,
            kb_fix_rows=kb_fix_rows,
            evidence_map=evidence_map,
            output_root=root / "search_context",
            manifest_output=manifest_output,
        )
        _assert(report.status == "ACTUAL_CORPUS_SEARCH_CONTEXT_EXTRACTED", report.status)
        _assert(report.ready_for_search_context_extraction is True, "should be ready")
        _assert(report.matched_row_count == 0, str(report.matched_row_count))
        _assert(report.artifact_count == 0, str(report.artifact_count))
        _assert(report.extraction_failed_count == 0, str(report.extraction_failed_count))
        _assert(manifest_output.exists(), "manifest must be written")


def run_validation() -> None:
    test_extraction_blocked_when_prerequisites_missing()
    test_extraction_runs_with_empty_evidence_map()
    print("[gate21h:search-context] OK")
    print("[gate21h:search-context] missing_prerequisites=blocked")
    print("[gate21h:search-context] empty_evidence_map=extracted")


if __name__ == "__main__":
    run_validation()
