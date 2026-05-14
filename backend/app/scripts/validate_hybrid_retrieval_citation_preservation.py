from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.hybrid_retrieval_citation_preservation_validator import (
    DEFAULT_CITATION_PRESERVATION_REPORT,
    REQUIRED_TRACE_FIELDS,
    HybridCitationCandidate,
    build_citation_preservation_report,
    fixture_candidates,
    read_json,
    validate_candidate_citations,
    write_citation_preservation_report,
)
from app.scripts.hybrid_retrieval_score_normalization_design import (
    DEFAULT_SCORE_NORMALIZATION_DESIGN,
    build_score_normalization_design,
    write_score_normalization_design,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_fixture_candidates_preserve_citations() -> None:
    root = repo_root()
    score_design = root / DEFAULT_SCORE_NORMALIZATION_DESIGN
    if not score_design.exists():
        write_score_normalization_design(
            score_design,
            build_score_normalization_design(
                fixture_merge_plan_path=root / "kbs" / "retrieval" / "kb_hybrid_retrieval_fixture_merge_plan.v1.json"
            ),
        )
    report = build_citation_preservation_report(score_design_path=score_design)
    if report.status != "HYBRID_CITATION_PRESERVATION_VALID":
        raise AssertionError(f"Unexpected report status: {report.status}")
    if report.candidate_count != 3:
        raise AssertionError(f"Expected 3 candidates, got: {report.candidate_count}")
    if report.missing_citation_count != 0:
        raise AssertionError("Expected zero missing citation payloads")
    if report.missing_trace_field_count != 0:
        raise AssertionError("Expected zero missing trace fields")
    if report.hybrid_merge_enabled is not False:
        raise AssertionError("Hybrid merge must remain disabled")
    if report.merged_results_written is not False:
        raise AssertionError("Merged results must not be written")
    for candidate in report.checked_candidates:
        for field_name in REQUIRED_TRACE_FIELDS:
            if not str(candidate.citation_payload.get(field_name) or ""):
                raise AssertionError(f"Missing trace field {field_name} in {candidate.candidate_id}")
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "citation_report.json"
        write_citation_preservation_report(output, report)
        persisted = read_json(output)
        if persisted.get("merged_results_written") is not False:
            raise AssertionError("Persisted report must not write merged results")


def assert_missing_citation_is_detected() -> None:
    candidates = fixture_candidates()
    bad = [
        HybridCitationCandidate(
            candidate_id=candidate.candidate_id,
            source_mode=candidate.source_mode,
            rank=candidate.rank,
            chunk_id=candidate.chunk_id,
            citation_payload={},
            bm25_score=candidate.bm25_score,
            vector_score=candidate.vector_score,
            normalized_score=candidate.normalized_score,
        )
        if index == 0
        else candidate
        for index, candidate in enumerate(candidates)
    ]
    missing_citations, missing_trace_fields = validate_candidate_citations(bad)
    if missing_citations != 1:
        raise AssertionError(f"Expected one missing citation payload, got: {missing_citations}")
    if missing_trace_fields != len(REQUIRED_TRACE_FIELDS):
        raise AssertionError(f"Expected all trace fields missing, got: {missing_trace_fields}")


def assert_missing_trace_field_is_detected() -> None:
    candidates = fixture_candidates()
    first = candidates[0]
    payload = dict(first.citation_payload)
    payload[REQUIRED_TRACE_FIELDS[0]] = ""
    bad = [
        HybridCitationCandidate(
            candidate_id=first.candidate_id,
            source_mode=first.source_mode,
            rank=first.rank,
            chunk_id=first.chunk_id,
            citation_payload=payload,
            bm25_score=first.bm25_score,
            vector_score=first.vector_score,
            normalized_score=first.normalized_score,
        ),
        *candidates[1:],
    ]
    missing_citations, missing_trace_fields = validate_candidate_citations(bad)
    if missing_citations != 0:
        raise AssertionError(f"Expected zero missing citation payloads, got: {missing_citations}")
    if missing_trace_fields != 1:
        raise AssertionError(f"Expected one missing trace field, got: {missing_trace_fields}")


def assert_bad_score_design_blocks_validation() -> None:
    root = repo_root()
    score_design = root / DEFAULT_SCORE_NORMALIZATION_DESIGN
    if not score_design.exists():
        write_score_normalization_design(
            score_design,
            build_score_normalization_design(
                fixture_merge_plan_path=root / "kbs" / "retrieval" / "kb_hybrid_retrieval_fixture_merge_plan.v1.json"
            ),
        )
    source = read_json(score_design)
    bad_cases = [
        ("status", "HYBRID_SCORE_NORMALIZATION_DESIGN_BLOCKED"),
        ("hybrid_merge_enabled", True),
        ("merged_results_written", True),
    ]
    for field_name, bad_value in bad_cases:
        bad = copy.deepcopy(source)
        bad[field_name] = bad_value
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_path = Path(temp_dir) / f"bad_{field_name}.json"
            write_json(bad_path, bad)
            try:
                build_citation_preservation_report(score_design_path=bad_path)
            except ValueError:
                continue
            raise AssertionError(f"Bad score design field must block citation validation: {field_name}")


def main() -> None:
    assert_fixture_candidates_preserve_citations()
    assert_missing_citation_is_detected()
    assert_missing_trace_field_is_detected()
    assert_bad_score_design_blocks_validation()
    print("[gate19d:citation] OK")
    print("[gate19d:citation] citation_payloads=preserved")
    print("[gate19d:citation] trace_fields=complete")
    print("[gate19d:citation] missing_citation=detected")
    print("[gate19d:citation] merged_results_written=false")


if __name__ == "__main__":
    main()
