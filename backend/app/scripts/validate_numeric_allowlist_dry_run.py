from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.apply_numeric_allowlist_dry_run import (
    DEFAULT_RESPONSE_JSONL,
    DEFAULT_TRIAGE_REPORT,
    DEFAULT_VECTOR_INDEX_PATH,
    DEFAULT_VECTOR_PATH,
    ALLOWLIST_CLASS,
    build_numeric_allowlist_dry_run_report,
    write_numeric_allowlist_dry_run_report,
)
from app.scripts.extract_kb_source_manifest import repo_root


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def assert_report_applies_allowlist_to_dry_run_only() -> None:
    root = repo_root()
    triage_report = root / DEFAULT_TRIAGE_REPORT
    if not triage_report.exists():
        raise AssertionError(f"Expected Gate 18H triage report: {triage_report}")
    source = read_json(triage_report)
    source_findings = int(source.get("source_finding_count") or 0)
    source_allowlisted = int(source.get("allowlisted_finding_count") or 0)
    source_unresolved = int(source.get("unresolved_finding_count") or 0)

    report = build_numeric_allowlist_dry_run_report(triage_report_path=triage_report)
    if report.summary.source_finding_count != source_findings:
        raise AssertionError("Source finding count mismatch")
    if report.summary.allowlisted_finding_count != source_allowlisted:
        raise AssertionError("Allowlisted finding count mismatch")
    if report.summary.unresolved_finding_count != source_unresolved:
        raise AssertionError("Unresolved finding count mismatch")
    if report.summary.effective_blocking_finding_count != source_unresolved:
        raise AssertionError("Only unresolved findings should remain blocking")
    if ALLOWLIST_CLASS not in report.applied_classes:
        raise AssertionError(f"Expected applied allowlist class {ALLOWLIST_CLASS}")
    if report.real_submission_allowed is not False:
        raise AssertionError("Gate 18I must not allow real submission")
    if report.dry_run_only is not True:
        raise AssertionError("Gate 18I report must remain dry-run only")
    if report.vectors_created is not False:
        raise AssertionError("Gate 18I must not create vectors")
    if source_unresolved > 0 and report.status != "DRY_RUN_ALLOWLIST_APPLIED_BLOCKED":
        raise AssertionError(f"Expected blocked dry-run status, got: {report.status}")
    if source_unresolved == 0 and report.status != "DRY_RUN_ALLOWLIST_APPLIED_NO_BLOCKERS":
        raise AssertionError(f"Expected no-blockers dry-run status, got: {report.status}")

    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "allowlist_report.json"
        write_numeric_allowlist_dry_run_report(output, report)
        persisted = read_json(output)
        if persisted.get("real_submission_allowed") is not False:
            raise AssertionError("Persisted report must forbid real submission")
        summary = persisted.get("summary")
        if not isinstance(summary, dict):
            raise AssertionError("Persisted report missing summary")
        if summary.get("effective_blocking_finding_count") != source_unresolved:
            raise AssertionError("Persisted effective blocking count mismatch")


def assert_no_response_or_vector_outputs_exist() -> None:
    root = repo_root()
    for relative in (DEFAULT_RESPONSE_JSONL, DEFAULT_VECTOR_PATH, DEFAULT_VECTOR_INDEX_PATH):
        if (root / relative).exists():
            raise AssertionError(f"Gate 18I must not create response/vector artifact: {relative}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 18I numeric allowlist dry-run application.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_report_applies_allowlist_to_dry_run_only()
    assert_no_response_or_vector_outputs_exist()
    print("[gate18i:allowlist] OK")
    print("[gate18i:allowlist] allowlist=applied_to_dry_run")
    print("[gate18i:allowlist] unresolved_findings=remain_blocking")
    print("[gate18i:allowlist] real_submission_allowed=false")
    print("[gate18i:allowlist] vectors=not_created")


if __name__ == "__main__":
    main()
