from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.redaction_finding_triage_allowlist import (
    DEFAULT_FULL_TEXT_PAYLOAD_REPORT,
    DEFAULT_FULL_TEXT_REQUEST_JSONL,
    build_allowlist_policy,
    build_redaction_triage_report,
    classify_long_digit_value,
    write_redaction_triage_report,
)


DEFAULT_TRIAGE_REPORT = "kbs/retrieval/kb_embedding_redaction_triage_report.v1.json"
DEFAULT_RESPONSE_JSONL = "kbs/retrieval/kb_embedding_batch_responses.v1.jsonl"
DEFAULT_VECTOR_PATH = "kbs/retrieval/kb_vectors.v1.jsonl"
DEFAULT_VECTOR_INDEX_PATH = "kbs/retrieval/kb_vector_index.v1.json"


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def assert_classifier_cases() -> None:
    classification, _ = classify_long_digit_value(text="bug id 1234567890123 fixed in patch", value="1234567890123")
    if classification != "LIKELY_TECHNICAL_IDENTIFIER":
        raise AssertionError(f"Expected likely technical identifier, got: {classification}")
    classification, _ = classify_long_digit_value(text="misc number 1234567890123 appears alone", value="1234567890123")
    if classification != "UNRESOLVED_LONG_DIGIT_SEQUENCE":
        raise AssertionError(f"Expected unresolved long digit sequence, got: {classification}")


def assert_allowlist_policy_is_design_only() -> None:
    policy = build_allowlist_policy()
    if policy.status != "DESIGN_ONLY_NOT_APPLIED":
        raise AssertionError(f"Expected design-only policy, got: {policy}")
    if policy.embedding_submission_allowed is not False:
        raise AssertionError("Allowlist policy must not allow embedding submission.")
    if "UNRESOLVED_REQUIRES_REVIEW" not in policy.forbidden_classes:
        raise AssertionError(f"Expected unresolved class to be forbidden: {policy}")
    if policy.required_review_before_submission is not True:
        raise AssertionError("Policy must require review before submission.")


def assert_triage_report_builds_from_gate18f_outputs() -> None:
    root = repo_root()
    payload_report = root / DEFAULT_FULL_TEXT_PAYLOAD_REPORT
    request_jsonl = root / DEFAULT_FULL_TEXT_REQUEST_JSONL
    if not payload_report.exists():
        raise AssertionError(f"Expected Gate 18F payload report: {payload_report}")
    if not request_jsonl.exists():
        raise AssertionError(f"Expected Gate 18F request JSONL: {request_jsonl}")

    source_payload = read_json(payload_report)
    report = build_redaction_triage_report(payload_report_path=payload_report, request_jsonl_path=request_jsonl)
    if report.source_finding_count != int(source_payload.get("finding_count") or 0):
        raise AssertionError("Source finding count mismatch")
    if report.triaged_finding_count != report.source_finding_count:
        raise AssertionError("Triaged finding count must equal source finding count")
    if report.embedding_submission_allowed is not False:
        raise AssertionError("Triage report must not allow embedding submission")
    if report.vectors_created is not False:
        raise AssertionError("Triage report must not create vectors")
    if report.allowlist_policy.embedding_submission_allowed is not False:
        raise AssertionError("Allowlist policy in report must not allow submission")
    if report.source_finding_count > 0 and not report.findings:
        raise AssertionError("Expected triage findings when source findings exist")
    for finding in report.findings:
        if finding.classification not in {
            "ALLOWLIST_CANDIDATE_TECHNICAL_IDENTIFIER",
            "UNRESOLVED_REQUIRES_REVIEW",
            "FORBIDDEN_REQUIRES_REVIEW",
        }:
            raise AssertionError(f"Unexpected finding classification: {finding}")

    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "triage_report.json"
        write_redaction_triage_report(output, report)
        persisted = read_json(output)
        if persisted.get("triaged_finding_count") != report.triaged_finding_count:
            raise AssertionError("Persisted triage count mismatch")
        if persisted.get("embedding_submission_allowed") is not False:
            raise AssertionError("Persisted triage report must forbid embedding submission")


def assert_no_response_or_vector_outputs_exist() -> None:
    root = repo_root()
    for relative in (DEFAULT_RESPONSE_JSONL, DEFAULT_VECTOR_PATH, DEFAULT_VECTOR_INDEX_PATH):
        if (root / relative).exists():
            raise AssertionError(f"Gate 18H must not create response/vector artifact: {relative}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 18H redaction finding triage allowlist design.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_classifier_cases()
    assert_allowlist_policy_is_design_only()
    assert_triage_report_builds_from_gate18f_outputs()
    assert_no_response_or_vector_outputs_exist()
    print("[gate18h:triage] OK")
    print("[gate18h:triage] classifier=valid")
    print("[gate18h:triage] allowlist_policy=design_only")
    print("[gate18h:triage] findings=triaged")
    print("[gate18h:triage] embedding_submission=forbidden")
    print("[gate18h:triage] vectors=not_created")


if __name__ == "__main__":
    main()
