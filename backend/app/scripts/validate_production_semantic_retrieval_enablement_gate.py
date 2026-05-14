from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.hybrid_retrieval_citation_preservation_validator import (
    DEFAULT_CITATION_PRESERVATION_REPORT,
    build_citation_preservation_report,
    write_citation_preservation_report,
)
from app.scripts.production_semantic_retrieval_enablement_gate import (
    build_enablement_gate_report,
    read_json,
    write_enablement_gate_report,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_ready_citation_report() -> Path:
    root = repo_root()
    citation_report = root / DEFAULT_CITATION_PRESERVATION_REPORT
    if not citation_report.exists():
        write_citation_preservation_report(
            citation_report,
            build_citation_preservation_report(
                score_design_path=root / "kbs" / "retrieval" / "kb_hybrid_retrieval_score_normalization_design.v1.json"
            ),
        )
    return citation_report


def assert_default_gate_is_disabled() -> None:
    citation_report = ensure_ready_citation_report()
    report = build_enablement_gate_report(citation_preservation_path=citation_report)
    if report.status != "PRODUCTION_SEMANTIC_RETRIEVAL_DISABLED":
        raise AssertionError(f"Unexpected default status: {report.status}")
    if report.production_semantic_retrieval_enabled is not False:
        raise AssertionError("Production semantic retrieval must remain disabled")
    if report.hybrid_merge_enabled is not False:
        raise AssertionError("Hybrid merge must remain disabled")
    if report.vector_retrieval_authoritative is not False:
        raise AssertionError("Vector retrieval must not become authoritative")
    if report.bm25_authoritative is not True:
        raise AssertionError("BM25 must remain authoritative")
    if report.fail_closed is not True:
        raise AssertionError("Enablement gate must fail closed")
    if report.failed_count != 0:
        raise AssertionError(f"Expected zero failed checks, got: {report.failed_count}")
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "enablement.json"
        write_enablement_gate_report(output, report)
        persisted = read_json(output)
        if persisted.get("production_semantic_retrieval_enabled") is not False:
            raise AssertionError("Persisted report must keep production semantic retrieval disabled")


def assert_explicit_enablement_attempt_blocks() -> None:
    citation_report = ensure_ready_citation_report()
    report = build_enablement_gate_report(
        citation_preservation_path=citation_report,
        explicit_enablement_requested=True,
        operator_approval_recorded=True,
    )
    if report.status != "PRODUCTION_SEMANTIC_RETRIEVAL_ENABLEMENT_BLOCKED":
        raise AssertionError(f"Expected blocked status, got: {report.status}")
    if "explicit_enablement_not_requested" not in report.blockers:
        raise AssertionError(f"Expected explicit enablement blocker, got: {report.blockers}")
    if "operator_approval_absent" not in report.blockers:
        raise AssertionError(f"Expected operator approval blocker, got: {report.blockers}")
    if report.production_semantic_retrieval_enabled is not False:
        raise AssertionError("Blocked enablement must not enable production semantic retrieval")


def assert_bad_citation_report_blocks() -> None:
    source_path = ensure_ready_citation_report()
    source = read_json(source_path)
    bad_cases = [
        ("status", "HYBRID_CITATION_PRESERVATION_INVALID"),
        ("missing_citation_count", 1),
        ("missing_trace_field_count", 1),
        ("hybrid_merge_enabled", True),
        ("merged_results_written", True),
    ]
    for field_name, bad_value in bad_cases:
        bad = copy.deepcopy(source)
        bad[field_name] = bad_value
        with tempfile.TemporaryDirectory() as temp_dir:
            bad_path = Path(temp_dir) / f"bad_{field_name}.json"
            write_json(bad_path, bad)
            report = build_enablement_gate_report(citation_preservation_path=bad_path)
            if report.status != "PRODUCTION_SEMANTIC_RETRIEVAL_ENABLEMENT_BLOCKED":
                raise AssertionError(f"Expected blocked status for {field_name}, got: {report.status}")
            if report.production_semantic_retrieval_enabled is not False:
                raise AssertionError(f"Bad upstream report must not enable retrieval: {field_name}")


def main() -> None:
    assert_default_gate_is_disabled()
    assert_explicit_enablement_attempt_blocks()
    assert_bad_citation_report_blocks()
    print("[gate19e:enablement] OK")
    print("[gate19e:enablement] default=disabled")
    print("[gate19e:enablement] explicit_enablement=blocked")
    print("[gate19e:enablement] bad_upstream=blocked")
    print("[gate19e:enablement] production_semantic_retrieval_enabled=false")


if __name__ == "__main__":
    main()
