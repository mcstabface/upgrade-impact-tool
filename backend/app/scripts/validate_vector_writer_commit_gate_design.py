from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.vector_writer_commit_gate_design import (
    DEFAULT_VECTOR_DRY_RUN_REPORT,
    DEFAULT_VECTOR_INDEX_PATH,
    DEFAULT_VECTOR_PATH,
    build_vector_commit_gate_report,
    write_vector_commit_gate_report,
)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def assert_ready_dry_run_is_still_disabled() -> None:
    dry_run_report = repo_root() / DEFAULT_VECTOR_DRY_RUN_REPORT
    if not dry_run_report.exists():
        raise AssertionError(f"Expected Gate 18P dry-run report: {dry_run_report}")
    report = build_vector_commit_gate_report(dry_run_report_path=dry_run_report)
    if report.status != "COMMIT_GATE_READY_BUT_DISABLED":
        raise AssertionError(f"Expected ready-but-disabled status, got: {report.status}")
    if report.failed_count != 0:
        raise AssertionError(f"Expected zero failed checks, got: {report.failed_count}")
    if report.commit_enabled is not False:
        raise AssertionError("Gate 18Q must not enable vector commit")
    if report.vector_outputs_created is not False:
        raise AssertionError("Gate 18Q must not create vector outputs")
    if report.vector_jsonl_path != DEFAULT_VECTOR_PATH:
        raise AssertionError("Unexpected vector JSONL path")
    if report.vector_index_path != DEFAULT_VECTOR_INDEX_PATH:
        raise AssertionError("Unexpected vector index path")
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "commit_gate.json"
        write_vector_commit_gate_report(output, report)
        persisted = read_json(output)
        if persisted.get("commit_enabled") is not False:
            raise AssertionError("Persisted report must keep commit disabled")


def assert_blocked_dry_run_blocks_commit_gate() -> None:
    source = read_json(repo_root() / DEFAULT_VECTOR_DRY_RUN_REPORT)
    blocked = copy.deepcopy(source)
    blocked["status"] = "DRY_RUN_INVALID"
    blocked["validation_error_count"] = 1
    blocked["validation_errors"] = ["fixture error"]
    with tempfile.TemporaryDirectory() as temp_dir:
        dry_run = Path(temp_dir) / "blocked_dry_run.json"
        write_json(dry_run, blocked)
        report = build_vector_commit_gate_report(dry_run_report_path=dry_run)
        if report.status != "COMMIT_GATE_BLOCKED":
            raise AssertionError(f"Expected blocked status, got: {report.status}")
        if report.failed_count < 1:
            raise AssertionError("Expected at least one failed check")
        if "dry_run_report_valid" not in report.blockers:
            raise AssertionError(f"Expected dry_run_report_valid blocker, got: {report.blockers}")
        if report.commit_enabled is not False:
            raise AssertionError("Blocked gate must not enable commit")


def assert_no_vector_outputs_exist() -> None:
    root = repo_root()
    for relative in (DEFAULT_VECTOR_PATH, DEFAULT_VECTOR_INDEX_PATH):
        if (root / relative).exists():
            raise AssertionError(f"Gate 18Q must not create vector artifact: {relative}")


def main() -> None:
    assert_ready_dry_run_is_still_disabled()
    assert_blocked_dry_run_blocks_commit_gate()
    assert_no_vector_outputs_exist()
    print("[gate18q:commit-gate] OK")
    print("[gate18q:commit-gate] ready_state=disabled")
    print("[gate18q:commit-gate] blocked_state=fail_closed")
    print("[gate18q:commit-gate] commit_enabled=false")
    print("[gate18q:commit-gate] vectors=not_created")


if __name__ == "__main__":
    main()
