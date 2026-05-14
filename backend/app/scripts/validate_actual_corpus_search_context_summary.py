from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.scripts.actual_corpus_search_context_summary import build_summary_from_manifest
from app.scripts.extract_kb_source_manifest import repo_root


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _repo_tempdir() -> TemporaryDirectory[str]:
    return TemporaryDirectory(dir=repo_root())


def test_missing_manifest_blocks_summary() -> None:
    with _repo_tempdir() as tmp:
        missing = Path(tmp) / "missing_manifest.json"
        report = build_summary_from_manifest(
            manifest_path=missing,
            extraction_status="ACTUAL_CORPUS_SEARCH_CONTEXT_EXTRACTED",
        )
        _assert(report.status == "ACTUAL_CORPUS_SEARCH_CONTEXT_SUMMARY_BLOCKED", report.status)
        _assert(report.errors, "missing manifest must produce errors")
        _assert(report.artifact_count == 0, str(report.artifact_count))


def test_summary_ready_from_manifest() -> None:
    with _repo_tempdir() as tmp:
        manifest = Path(tmp) / "kb_search_context_manifest.json"
        manifest.write_text(
            json.dumps(
                {
                    "manifest_type": "kb_search_context_manifest.v1",
                    "evidence_map_path": "kbs/manifests/kb_evidence_map.json",
                    "output_root": "kbs/search_context",
                    "matched_row_count": 2,
                    "artifact_count": 2,
                    "extraction_failed_count": 0,
                    "empty_text_count": 0,
                    "image_bearing_artifact_count": 1,
                    "highlight_bearing_artifact_count": 0,
                    "warnings": ["sample warning"],
                    "artifacts": [
                        {
                            "artifact_path": "kbs/search_context/KB1/a.json",
                            "kb_document_id": "KB1",
                            "bug_patch_number": "BUG-1",
                            "product": "Product A",
                            "category": "Fix",
                            "char_count": 100,
                            "page_count": 2,
                            "has_images": False,
                            "has_highlight_annotations": False,
                        },
                        {
                            "artifact_path": "kbs/search_context/KB2/b.json",
                            "kb_document_id": "KB2",
                            "bug_patch_number": "BUG-2",
                            "product": "Product B",
                            "category": "Fix",
                            "char_count": 300,
                            "page_count": 4,
                            "has_images": True,
                            "has_highlight_annotations": False,
                        },
                    ],
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        report = build_summary_from_manifest(
            manifest_path=manifest,
            extraction_status="ACTUAL_CORPUS_SEARCH_CONTEXT_EXTRACTED",
        )
        _assert(report.status == "ACTUAL_CORPUS_SEARCH_CONTEXT_SUMMARY_READY", report.status)
        _assert(report.artifact_count == 2, str(report.artifact_count))
        _assert(report.total_char_count == 400, str(report.total_char_count))
        _assert(report.total_page_count == 6, str(report.total_page_count))
        _assert(report.average_char_count == 200.0, str(report.average_char_count))
        _assert(report.demo_candidate_count == 2, str(report.demo_candidate_count))
        _assert(report.demo_candidates[0].kb_document_id == "KB2", report.demo_candidates)


def run_validation() -> None:
    test_missing_manifest_blocks_summary()
    test_summary_ready_from_manifest()
    print("[gate21i:search-context-summary] OK")
    print("[gate21i:search-context-summary] missing_manifest=blocked")
    print("[gate21i:search-context-summary] populated_manifest=summary_ready")


if __name__ == "__main__":
    run_validation()
