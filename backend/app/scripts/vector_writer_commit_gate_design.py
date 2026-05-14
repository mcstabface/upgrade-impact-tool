from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_VECTOR_DRY_RUN_REPORT = "kbs/retrieval/kb_vector_writer_dry_run_report.v1.json"
DEFAULT_COMMIT_GATE_REPORT = "kbs/retrieval/kb_vector_writer_commit_gate.v1.json"
DEFAULT_VECTOR_PATH = "kbs/retrieval/kb_vectors.v1.jsonl"
DEFAULT_VECTOR_INDEX_PATH = "kbs/retrieval/kb_vector_index.v1.json"


@dataclass(frozen=True)
class VectorCommitGateCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class VectorCommitGateReport:
    report_version: str
    status: str
    source_dry_run_report: str
    checks: list[VectorCommitGateCheck]
    passed_count: int
    failed_count: int
    commit_enabled: bool = False
    vector_outputs_created: bool = False
    vector_jsonl_path: str = DEFAULT_VECTOR_PATH
    vector_index_path: str = DEFAULT_VECTOR_INDEX_PATH
    blockers: list[str] = field(default_factory=list)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def build_vector_commit_gate_report(*, dry_run_report_path: Path) -> VectorCommitGateReport:
    if not dry_run_report_path.exists():
        raise FileNotFoundError(f"Vector dry-run report not found: {dry_run_report_path}")
    dry_run = read_json(dry_run_report_path)
    checks: list[VectorCommitGateCheck] = []
    blockers: list[str] = []

    def add_check(name: str, passed: bool, detail: str) -> None:
        checks.append(VectorCommitGateCheck(name=name, passed=passed, detail=detail))
        if not passed:
            blockers.append(name)

    add_check("dry_run_report_valid", dry_run.get("status") == "DRY_RUN_VALID", f"status={dry_run.get('status')}")
    add_check("dry_run_only", dry_run.get("dry_run_only") is True, f"dry_run_only={dry_run.get('dry_run_only')}")
    add_check(
        "candidate_vectors_present",
        int(dry_run.get("candidate_vector_count") or 0) > 0,
        f"candidate_vector_count={dry_run.get('candidate_vector_count')}",
    )
    add_check(
        "validation_errors_absent",
        int(dry_run.get("validation_error_count") or 0) == 0,
        f"validation_error_count={dry_run.get('validation_error_count')}",
    )
    add_check(
        "dry_run_vector_outputs_absent",
        dry_run.get("vector_outputs_created") is False,
        f"vector_outputs_created={dry_run.get('vector_outputs_created')}",
    )
    add_check(
        "vector_paths_declared",
        dry_run.get("vector_jsonl_path") == DEFAULT_VECTOR_PATH and dry_run.get("vector_index_path") == DEFAULT_VECTOR_INDEX_PATH,
        f"vector_jsonl_path={dry_run.get('vector_jsonl_path')} vector_index_path={dry_run.get('vector_index_path')}",
    )

    failed_count = sum(1 for check in checks if not check.passed)
    passed_count = len(checks) - failed_count
    root = repo_root()
    source_dry_run_report = str(dry_run_report_path.relative_to(root)) if dry_run_report_path.is_relative_to(root) else str(dry_run_report_path)
    return VectorCommitGateReport(
        report_version="1",
        status="COMMIT_GATE_READY_BUT_DISABLED" if failed_count == 0 else "COMMIT_GATE_BLOCKED",
        source_dry_run_report=source_dry_run_report,
        checks=checks,
        passed_count=passed_count,
        failed_count=failed_count,
        commit_enabled=False,
        vector_outputs_created=False,
        blockers=blockers,
    )


def write_vector_commit_gate_report(path: Path, report: VectorCommitGateReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build Gate 18Q vector writer commit gate design report.")
    parser.add_argument("--dry-run-report", type=Path, default=root / DEFAULT_VECTOR_DRY_RUN_REPORT)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_COMMIT_GATE_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_vector_commit_gate_report(dry_run_report_path=args.dry_run_report)
    write_vector_commit_gate_report(args.output, report)
    print(f"[gate18q:commit-gate] Wrote commit gate report: {args.output}")
    print(f"[gate18q:commit-gate] status={report.status}")
    print(f"[gate18q:commit-gate] passed_checks={report.passed_count}")
    print(f"[gate18q:commit-gate] failed_checks={report.failed_count}")
    print("[gate18q:commit-gate] commit_enabled=false")
    print("[gate18q:commit-gate] vectors=not_created")


if __name__ == "__main__":
    main()
