from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory

from app.scripts.actual_corpus_demo_readiness import build_actual_corpus_demo_readiness_report


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def test_missing_corpus_root_not_ready() -> None:
    with TemporaryDirectory() as tmp:
        missing = Path(tmp) / "missing"
        report = build_actual_corpus_demo_readiness_report(corpus_root=missing)
        _assert(report.status == "ACTUAL_CORPUS_NOT_READY", report.status)
        _assert(report.corpus_root_exists is False, "missing root must be false")
        _assert(report.file_count == 0, str(report.file_count))
        _assert(report.errors, "missing root must produce errors")


def test_empty_corpus_root_not_ready() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp) / "corpus"
        root.mkdir()
        report = build_actual_corpus_demo_readiness_report(corpus_root=root)
        _assert(report.status == "ACTUAL_CORPUS_NOT_READY", report.status)
        _assert(report.corpus_root_exists is True, "root exists")
        _assert(report.file_count == 0, str(report.file_count))
        _assert(report.demo_readiness_checks["has_files"] == "FAIL", report.demo_readiness_checks)


def test_populated_corpus_ready_for_ingestion_assessment() -> None:
    with TemporaryDirectory() as tmp:
        root = Path(tmp) / "corpus"
        nested = root / "nested"
        nested.mkdir(parents=True)
        (root / "alpha.txt").write_text("alpha", encoding="utf-8")
        (nested / "beta.md").write_text("beta", encoding="utf-8")
        (nested / "README").write_text("gamma", encoding="utf-8")
        report = build_actual_corpus_demo_readiness_report(corpus_root=root, sample_limit=2)
        _assert(report.status == "ACTUAL_CORPUS_READY_FOR_INGESTION_ASSESSMENT", report.status)
        _assert(report.corpus_root_exists is True, "root exists")
        _assert(report.file_count == 3, str(report.file_count))
        _assert(report.extension_counts[".txt"] == 1, report.extension_counts)
        _assert(report.extension_counts[".md"] == 1, report.extension_counts)
        _assert(report.extension_counts["[no_extension]"] == 1, report.extension_counts)
        _assert(len(report.sample_files) == 2, str(len(report.sample_files)))
        _assert(report.demo_readiness_checks["has_files"] == "PASS", report.demo_readiness_checks)
        _assert(report.recommended_next_steps, "next steps must be populated")


def run_validation() -> None:
    test_missing_corpus_root_not_ready()
    test_empty_corpus_root_not_ready()
    test_populated_corpus_ready_for_ingestion_assessment()
    print("[gate21c:actual-corpus] OK")
    print("[gate21c:actual-corpus] missing_root=not_ready")
    print("[gate21c:actual-corpus] empty_root=not_ready")
    print("[gate21c:actual-corpus] populated_root=ready_for_ingestion_assessment")


if __name__ == "__main__":
    run_validation()
