from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from app.scripts.actual_corpus_prerequisite_regeneration import build_actual_corpus_prerequisite_regeneration_report
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
    for path in (portfolio_extraction, kb_fix_rows, evidence_map):
        path.write_text("{}\n", encoding="utf-8")
    return portfolio_extraction, kb_fix_rows, evidence_map


def test_regeneration_ready_when_downstream_prerequisites_exist() -> None:
    with _repo_tempdir() as tmp:
        root = Path(tmp)
        source = root / "raw"
        _write_source_fixture(source)
        inventory = root / "actual_corpus_source_inventory.json"
        portfolio_extraction, kb_fix_rows, evidence_map = _write_prerequisites(root)
        report = build_actual_corpus_prerequisite_regeneration_report(
            source_root=source,
            inventory_output=inventory,
            portfolio_extraction=portfolio_extraction,
            kb_fix_rows=kb_fix_rows,
            evidence_map=evidence_map,
            search_context_output_root=root / "search_context",
            search_context_manifest=root / "kb_search_context_manifest.json",
        )
        _assert(report.status == "ACTUAL_CORPUS_PREREQUISITES_REGENERATED_READY", report.status)
        _assert(report.source_inventory_status == "ACTUAL_CORPUS_SOURCE_INVENTORY_EXTRACTED", report.source_inventory_status)
        _assert(report.ready_for_search_context_extraction is True, "should be ready")
        _assert(report.missing_prerequisites == [], report.missing_prerequisites)
        _assert(inventory.exists(), "inventory must be regenerated")


def test_regeneration_blocked_when_downstream_prerequisite_missing() -> None:
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
        report = build_actual_corpus_prerequisite_regeneration_report(
            source_root=source,
            inventory_output=inventory,
            portfolio_extraction=portfolio_extraction,
            kb_fix_rows=kb_fix_rows,
            evidence_map=evidence_map,
            search_context_output_root=root / "search_context",
            search_context_manifest=root / "kb_search_context_manifest.json",
        )
        _assert(report.status == "ACTUAL_CORPUS_PREREQUISITES_REGENERATION_BLOCKED", report.status)
        _assert(report.ready_for_search_context_extraction is False, "should not be ready")
        _assert(report.missing_prerequisites == ["kb_evidence_map"], report.missing_prerequisites)
        _assert(inventory.exists(), "inventory should still be regenerated")


def run_validation() -> None:
    test_regeneration_ready_when_downstream_prerequisites_exist()
    test_regeneration_blocked_when_downstream_prerequisite_missing()
    print("[gate21g:prereq-regen] OK")
    print("[gate21g:prereq-regen] all_prerequisites=ready")
    print("[gate21g:prereq-regen] missing_downstream_prerequisite=blocked")


if __name__ == "__main__":
    run_validation()
