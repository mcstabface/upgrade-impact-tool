from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from app.scripts.actual_corpus_source_inventory_extraction import extract_actual_corpus_source_inventory
from app.scripts.extract_kb_source_manifest import repo_root


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _repo_tempdir() -> TemporaryDirectory[str]:
    return TemporaryDirectory(dir=repo_root())


def test_missing_source_root_fails() -> None:
    with _repo_tempdir() as tmp:
        root = Path(tmp)
        missing = root / "missing"
        output = root / "inventory.json"
        report = extract_actual_corpus_source_inventory(source_root=missing, inventory_output=output)
        _assert(report.status == "ACTUAL_CORPUS_SOURCE_INVENTORY_EXTRACTION_FAILED", report.status)
        _assert(report.source_root_exists is False, "missing source root must be false")
        _assert(report.errors, "missing root must produce errors")
        _assert(not output.exists(), "missing root must not write inventory")


def test_empty_source_root_fails_but_writes_manifest() -> None:
    with _repo_tempdir() as tmp:
        root = Path(tmp)
        source = root / "raw"
        source.mkdir()
        output = root / "inventory.json"
        report = extract_actual_corpus_source_inventory(source_root=source, inventory_output=output)
        _assert(report.status == "ACTUAL_CORPUS_SOURCE_INVENTORY_EXTRACTION_FAILED", report.status)
        _assert(report.source_root_exists is True, "source root exists")
        _assert(report.html_source_count == 0, str(report.html_source_count))
        _assert(report.portfolio_file_count == 0, str(report.portfolio_file_count))
        _assert(report.errors, "empty source must produce errors")
        _assert(output.exists(), "empty source should still write manifest for inspection")


def test_populated_source_root_extracts_inventory() -> None:
    with _repo_tempdir() as tmp:
        root = Path(tmp)
        source = root / "raw"
        source.mkdir()
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
        output = root / "inventory.json"
        report = extract_actual_corpus_source_inventory(source_root=source, inventory_output=output)
        _assert(report.status == "ACTUAL_CORPUS_SOURCE_INVENTORY_EXTRACTED", report.status)
        _assert(report.source_root_exists is True, "source root exists")
        _assert(report.html_source_count == 1, str(report.html_source_count))
        _assert(report.portfolio_file_count == 1, str(report.portfolio_file_count))
        _assert(report.kb_document_count == 1, str(report.kb_document_count))
        _assert(report.missing_portfolio_count == 0, str(report.missing_portfolio_count))
        _assert(report.unreferenced_portfolio_count == 0, str(report.unreferenced_portfolio_count))
        _assert(output.exists(), "inventory manifest must be written")


def run_validation() -> None:
    test_missing_source_root_fails()
    test_empty_source_root_fails_but_writes_manifest()
    test_populated_source_root_extracts_inventory()
    print("[gate21e:source-inventory] OK")
    print("[gate21e:source-inventory] missing_root=failed")
    print("[gate21e:source-inventory] empty_root=failed_with_manifest")
    print("[gate21e:source-inventory] populated_root=extracted")


if __name__ == "__main__":
    run_validation()
