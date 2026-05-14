from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from app.scripts.actual_corpus_ingestion_dry_run import build_actual_corpus_ingestion_dry_run_report
from app.scripts.extract_kb_source_manifest import repo_root


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _repo_tempdir() -> TemporaryDirectory[str]:
    return TemporaryDirectory(dir=repo_root())


def test_missing_source_root_not_ready() -> None:
    with _repo_tempdir() as tmp:
        missing = Path(tmp) / "missing"
        report = build_actual_corpus_ingestion_dry_run_report(source_root=missing)
        _assert(report.status == "ACTUAL_CORPUS_INGESTION_DRY_RUN_NOT_READY", report.status)
        _assert(report.source_root_exists is False, "missing root must be false")
        _assert(report.dry_run_checks["source_root_exists"] == "FAIL", report.dry_run_checks)
        _assert(report.errors, "missing root must produce errors")


def test_empty_source_root_not_ready() -> None:
    with _repo_tempdir() as tmp:
        root = Path(tmp) / "raw"
        root.mkdir()
        report = build_actual_corpus_ingestion_dry_run_report(source_root=root)
        _assert(report.status == "ACTUAL_CORPUS_INGESTION_DRY_RUN_NOT_READY", report.status)
        _assert(report.source_root_exists is True, "root exists")
        _assert(report.html_source_count == 0, str(report.html_source_count))
        _assert(report.portfolio_file_count == 0, str(report.portfolio_file_count))
        _assert(report.dry_run_checks["manifest_buildable"] == "PASS", report.dry_run_checks)
        _assert(report.errors, "empty root must produce errors")


def test_populated_source_root_ready_with_no_missing_portfolios() -> None:
    with _repo_tempdir() as tmp:
        root = Path(tmp) / "raw"
        root.mkdir()
        portfolio = root / "CCS_1.0_MP1_PFDs_Portfolio.pdf"
        portfolio.write_bytes(b"%PDF-1.4\n%%EOF\n")
        html = root / "KB12345.html"
        html.write_text(
            """
            <html><body>
            <a href="https://example.test/?documentId=KB12345">KB12345</a>
            Hot Fix Release 1 About Window: CCS_1.0_MP1_PFDs_Portfolio.pdf
            </body></html>
            """,
            encoding="utf-8",
        )
        report = build_actual_corpus_ingestion_dry_run_report(source_root=root)
        _assert(report.status == "ACTUAL_CORPUS_INGESTION_DRY_RUN_READY", report.status)
        _assert(report.html_source_count == 1, str(report.html_source_count))
        _assert(report.portfolio_file_count == 1, str(report.portfolio_file_count))
        _assert(report.missing_portfolio_count == 0, str(report.missing_portfolio_count))
        _assert(report.kb_document_count == 1, str(report.kb_document_count))
        _assert(report.dry_run_checks["has_html_sources"] == "PASS", report.dry_run_checks)
        _assert(report.dry_run_checks["has_portfolio_files"] == "PASS", report.dry_run_checks)


def run_validation() -> None:
    test_missing_source_root_not_ready()
    test_empty_source_root_not_ready()
    test_populated_source_root_ready_with_no_missing_portfolios()
    print("[gate21d:ingestion-dry-run] OK")
    print("[gate21d:ingestion-dry-run] missing_root=not_ready")
    print("[gate21d:ingestion-dry-run] empty_root=not_ready")
    print("[gate21d:ingestion-dry-run] populated_root=ready")


if __name__ == "__main__":
    run_validation()
