from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_FULL_TEXT_REQUEST_JSONL = "kbs/retrieval/kb_embedding_full_text_requests.v1.jsonl"
DEFAULT_FULL_TEXT_PAYLOAD_REPORT = "kbs/retrieval/kb_embedding_full_text_payload_report.v1.json"
DEFAULT_DRY_RUN_SUBMISSION_REPORT = "kbs/retrieval/kb_embedding_dry_run_submission_report.v1.json"
DEFAULT_RESPONSE_JSONL = "kbs/retrieval/kb_embedding_batch_responses.v1.jsonl"
DEFAULT_VECTOR_PATH = "kbs/retrieval/kb_vectors.v1.jsonl"
DEFAULT_VECTOR_INDEX_PATH = "kbs/retrieval/kb_vector_index.v1.json"


@dataclass(frozen=True)
class DryRunSubmissionDecision:
    status: str
    reason: str
    request_count: int
    finding_count: int
    would_submit: bool = False
    real_submission_allowed: bool = False


@dataclass(frozen=True)
class DryRunSubmissionReport:
    report_version: str
    status: str
    source_request_jsonl: str
    source_payload_report: str
    request_count: int
    finding_count: int
    dry_run_only: bool
    would_submit: bool
    real_submission_allowed: bool
    decision: DryRunSubmissionDecision
    simulated_response_schema: dict[str, Any] = field(default_factory=dict)
    vectors_created: bool = False


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def read_jsonl_count(path: Path) -> int:
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"Expected JSON object row: {path}")
            count += 1
    return count


def build_dry_run_submission_decision(*, request_count: int, finding_count: int) -> DryRunSubmissionDecision:
    if request_count <= 0:
        return DryRunSubmissionDecision(
            status="REFUSED",
            reason="NO_REQUESTS",
            request_count=request_count,
            finding_count=finding_count,
        )
    if finding_count > 0:
        return DryRunSubmissionDecision(
            status="REFUSED",
            reason="REDACTION_FINDINGS_PRESENT",
            request_count=request_count,
            finding_count=finding_count,
        )
    return DryRunSubmissionDecision(
        status="DRY_RUN_READY",
        reason="NO_BLOCKING_FINDINGS_BUT_REAL_SUBMISSION_DISABLED",
        request_count=request_count,
        finding_count=finding_count,
        would_submit=True,
        real_submission_allowed=False,
    )


def simulated_response_schema() -> dict[str, Any]:
    return {
        "response_jsonl_path": DEFAULT_RESPONSE_JSONL,
        "row_contract": {
            "request_id": "string",
            "chunk_id": "string",
            "embedding_cache_key": "string",
            "model": "string",
            "dimensions": "integer",
            "embedding_vector": "array<float>",
            "status": "OK|ERROR",
            "error": "string|null",
        },
        "vector_store_outputs": {
            "vector_jsonl_path": DEFAULT_VECTOR_PATH,
            "vector_index_path": DEFAULT_VECTOR_INDEX_PATH,
        },
    }


def build_dry_run_submission_report(
    *,
    request_jsonl_path: Path,
    payload_report_path: Path,
) -> DryRunSubmissionReport:
    if not request_jsonl_path.exists():
        raise FileNotFoundError(f"Full-text request JSONL not found: {request_jsonl_path}")
    if not payload_report_path.exists():
        raise FileNotFoundError(f"Payload report not found: {payload_report_path}")

    request_count = read_jsonl_count(request_jsonl_path)
    payload_report = read_json(payload_report_path)
    report_request_count = int(payload_report.get("request_count") or 0)
    finding_count = int(payload_report.get("finding_count") or 0)
    if report_request_count != request_count:
        raise ValueError(f"Request count mismatch: JSONL has {request_count}, payload report has {report_request_count}")
    if payload_report.get("embedding_submission_allowed") is not False:
        raise ValueError("Gate 18F payload report must keep embedding_submission_allowed false")

    decision = build_dry_run_submission_decision(request_count=request_count, finding_count=finding_count)
    root = repo_root()
    source_request_jsonl = str(request_jsonl_path.relative_to(root)) if request_jsonl_path.is_relative_to(root) else str(request_jsonl_path)
    source_payload_report = str(payload_report_path.relative_to(root)) if payload_report_path.is_relative_to(root) else str(payload_report_path)
    return DryRunSubmissionReport(
        report_version="1",
        status=decision.status,
        source_request_jsonl=source_request_jsonl,
        source_payload_report=source_payload_report,
        request_count=request_count,
        finding_count=finding_count,
        dry_run_only=True,
        would_submit=decision.would_submit,
        real_submission_allowed=False,
        decision=decision,
        simulated_response_schema=simulated_response_schema(),
        vectors_created=False,
    )


def write_dry_run_submission_report(path: Path, report: DryRunSubmissionReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build Gate 18G dry-run embedding submission report without submitting requests.")
    parser.add_argument("--request-jsonl", type=Path, default=root / DEFAULT_FULL_TEXT_REQUEST_JSONL)
    parser.add_argument("--payload-report", type=Path, default=root / DEFAULT_FULL_TEXT_PAYLOAD_REPORT)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_DRY_RUN_SUBMISSION_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_dry_run_submission_report(
        request_jsonl_path=args.request_jsonl,
        payload_report_path=args.payload_report,
    )
    write_dry_run_submission_report(args.output, report)
    print(f"[gate18g:dry-run] Wrote dry-run submission report: {args.output}")
    print(f"[gate18g:dry-run] requests={report.request_count}")
    print(f"[gate18g:dry-run] redaction_findings={report.finding_count}")
    print(f"[gate18g:dry-run] status={report.status}")
    print("[gate18g:dry-run] real_submission_allowed=false")
    print("[gate18g:dry-run] vectors=not_created")


if __name__ == "__main__":
    main()
