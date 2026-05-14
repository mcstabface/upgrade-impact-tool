from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_TRIAGE_REPORT = "kbs/retrieval/kb_embedding_redaction_triage_report.v1.json"
DEFAULT_ALLOWLIST_APPLIED_REPORT = "kbs/retrieval/kb_embedding_numeric_allowlist_dry_run_report.v1.json"
DEFAULT_RESPONSE_JSONL = "kbs/retrieval/kb_embedding_batch_responses.v1.jsonl"
DEFAULT_VECTOR_PATH = "kbs/retrieval/kb_vectors.v1.jsonl"
DEFAULT_VECTOR_INDEX_PATH = "kbs/retrieval/kb_vector_index.v1.json"

ALLOWLIST_CLASS = "ALLOWLIST_CANDIDATE_TECHNICAL_IDENTIFIER"


@dataclass(frozen=True)
class NumericAllowlistDryRunSummary:
    source_finding_count: int
    allowlisted_finding_count: int
    unresolved_finding_count: int
    effective_blocking_finding_count: int


@dataclass(frozen=True)
class NumericAllowlistDryRunReport:
    report_version: str
    status: str
    source_triage_report: str
    applied_classes: list[str]
    blocked_classes: list[str]
    summary: NumericAllowlistDryRunSummary
    allowlisted_chunk_ids: list[str] = field(default_factory=list)
    unresolved_chunk_ids: list[str] = field(default_factory=list)
    real_submission_allowed: bool = False
    dry_run_only: bool = True
    vectors_created: bool = False


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def build_numeric_allowlist_dry_run_report(*, triage_report_path: Path) -> NumericAllowlistDryRunReport:
    if not triage_report_path.exists():
        raise FileNotFoundError(f"Redaction triage report not found: {triage_report_path}")
    triage = read_json(triage_report_path)
    findings = triage.get("findings")
    if not isinstance(findings, list):
        raise ValueError("Triage report findings must be a list")

    allowlisted_chunk_ids: list[str] = []
    unresolved_chunk_ids: list[str] = []
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError("Triage finding must be an object")
        chunk_id = str(finding.get("chunk_id") or "")
        classification = str(finding.get("classification") or "")
        if not chunk_id:
            raise ValueError("Triage finding missing chunk_id")
        if classification == ALLOWLIST_CLASS:
            allowlisted_chunk_ids.append(chunk_id)
        else:
            unresolved_chunk_ids.append(chunk_id)

    source_finding_count = int(triage.get("source_finding_count") or len(findings))
    if source_finding_count != len(findings):
        raise ValueError(f"source_finding_count mismatch: {source_finding_count} vs {len(findings)}")

    allowlisted_count = len(allowlisted_chunk_ids)
    unresolved_count = len(unresolved_chunk_ids)
    effective_blocking_count = unresolved_count
    status = "DRY_RUN_ALLOWLIST_APPLIED_BLOCKED" if effective_blocking_count else "DRY_RUN_ALLOWLIST_APPLIED_NO_BLOCKERS"

    root = repo_root()
    source_triage_report = str(triage_report_path.relative_to(root)) if triage_report_path.is_relative_to(root) else str(triage_report_path)
    return NumericAllowlistDryRunReport(
        report_version="1",
        status=status,
        source_triage_report=source_triage_report,
        applied_classes=[ALLOWLIST_CLASS],
        blocked_classes=["UNRESOLVED_REQUIRES_REVIEW", "FORBIDDEN_REQUIRES_REVIEW"],
        summary=NumericAllowlistDryRunSummary(
            source_finding_count=source_finding_count,
            allowlisted_finding_count=allowlisted_count,
            unresolved_finding_count=unresolved_count,
            effective_blocking_finding_count=effective_blocking_count,
        ),
        allowlisted_chunk_ids=sorted(allowlisted_chunk_ids),
        unresolved_chunk_ids=sorted(unresolved_chunk_ids),
        real_submission_allowed=False,
        dry_run_only=True,
        vectors_created=False,
    )


def write_numeric_allowlist_dry_run_report(path: Path, report: NumericAllowlistDryRunReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Apply Gate 18I numeric identifier allowlist candidates to dry-run reporting only.")
    parser.add_argument("--triage-report", type=Path, default=root / DEFAULT_TRIAGE_REPORT)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_ALLOWLIST_APPLIED_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_numeric_allowlist_dry_run_report(triage_report_path=args.triage_report)
    write_numeric_allowlist_dry_run_report(args.output, report)
    print(f"[gate18i:allowlist] Wrote numeric allowlist dry-run report: {args.output}")
    print(f"[gate18i:allowlist] source_findings={report.summary.source_finding_count}")
    print(f"[gate18i:allowlist] allowlisted_findings={report.summary.allowlisted_finding_count}")
    print(f"[gate18i:allowlist] unresolved_findings={report.summary.unresolved_finding_count}")
    print(f"[gate18i:allowlist] effective_blocking_findings={report.summary.effective_blocking_finding_count}")
    print("[gate18i:allowlist] real_submission_allowed=false")
    print("[gate18i:allowlist] vectors=not_created")


if __name__ == "__main__":
    main()
