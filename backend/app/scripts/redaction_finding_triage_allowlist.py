from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_FULL_TEXT_REQUEST_JSONL = "kbs/retrieval/kb_embedding_full_text_requests.v1.jsonl"
DEFAULT_FULL_TEXT_PAYLOAD_REPORT = "kbs/retrieval/kb_embedding_full_text_payload_report.v1.json"
DEFAULT_TRIAGE_REPORT = "kbs/retrieval/kb_embedding_redaction_triage_report.v1.json"

LONG_DIGIT_RE = re.compile(r"\b\d{13,19}\b")
KNOWN_TECHNICAL_CONTEXT_TERMS = (
    "bug",
    "patch",
    "kb",
    "document",
    "source",
    "sha",
    "hash",
    "id",
    "identifier",
    "case",
    "version",
    "build",
    "release",
)


@dataclass(frozen=True)
class RedactionTriageFinding:
    code: str
    chunk_id: str
    classification: str
    rationale: str
    matched_values: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class RedactionAllowlistPolicy:
    policy_version: str
    status: str
    allowed_classes: list[str]
    forbidden_classes: list[str]
    required_review_before_submission: bool
    embedding_submission_allowed: bool = False


@dataclass(frozen=True)
class RedactionTriageReport:
    report_version: str
    status: str
    source_payload_report: str
    source_request_jsonl: str
    source_finding_count: int
    triaged_finding_count: int
    unresolved_finding_count: int
    allowlisted_finding_count: int
    findings: list[RedactionTriageFinding]
    allowlist_policy: RedactionAllowlistPolicy
    embedding_submission_allowed: bool = False
    vectors_created: bool = False


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object row: {path}")
        rows.append(payload)
    return rows


def context_window(text: str, value: str, radius: int = 80) -> str:
    index = text.find(value)
    if index < 0:
        return ""
    start = max(0, index - radius)
    end = min(len(text), index + len(value) + radius)
    return text[start:end].lower()


def classify_long_digit_value(*, text: str, value: str) -> tuple[str, str]:
    window = context_window(text, value)
    if any(term in window for term in KNOWN_TECHNICAL_CONTEXT_TERMS):
        return "LIKELY_TECHNICAL_IDENTIFIER", "Long digit sequence appears near technical identifier context."
    return "UNRESOLVED_LONG_DIGIT_SEQUENCE", "Long digit sequence lacks enough local technical context for automatic allowlisting."


def build_request_text_by_chunk_id(request_rows: list[dict[str, Any]]) -> dict[str, str]:
    by_chunk_id: dict[str, str] = {}
    for row in request_rows:
        chunk_id = str(row.get("chunk_id") or "")
        input_text = str(row.get("input_text") or "")
        if not chunk_id:
            raise ValueError("Request row missing chunk_id")
        if chunk_id in by_chunk_id:
            raise ValueError(f"Duplicate request chunk_id: {chunk_id}")
        by_chunk_id[chunk_id] = input_text
    return by_chunk_id


def triage_payload_findings(*, payload_report: dict[str, Any], request_rows: list[dict[str, Any]]) -> list[RedactionTriageFinding]:
    findings = payload_report.get("findings")
    if not isinstance(findings, list):
        raise ValueError("Payload report findings must be a list")
    text_by_chunk_id = build_request_text_by_chunk_id(request_rows)
    triaged: list[RedactionTriageFinding] = []
    for finding in findings:
        if not isinstance(finding, dict):
            raise ValueError("Payload report finding must be an object")
        code = str(finding.get("code") or "")
        chunk_id = str(finding.get("chunk_id") or "")
        text = text_by_chunk_id.get(chunk_id, "")
        if code == "LONG_DIGIT_PATTERN":
            values = sorted(set(LONG_DIGIT_RE.findall(text)))
            classifications = [classify_long_digit_value(text=text, value=value) for value in values]
            if classifications and all(classification == "LIKELY_TECHNICAL_IDENTIFIER" for classification, _ in classifications):
                classification = "ALLOWLIST_CANDIDATE_TECHNICAL_IDENTIFIER"
                rationale = "All matched long digit sequences appear in technical identifier context."
            else:
                classification = "UNRESOLVED_REQUIRES_REVIEW"
                rationale = "One or more long digit sequences require manual review before allowlisting."
            triaged.append(
                RedactionTriageFinding(
                    code=code,
                    chunk_id=chunk_id,
                    classification=classification,
                    rationale=rationale,
                    matched_values=values,
                )
            )
        else:
            triaged.append(
                RedactionTriageFinding(
                    code=code,
                    chunk_id=chunk_id,
                    classification="FORBIDDEN_REQUIRES_REVIEW",
                    rationale="Non-long-digit redaction finding cannot be automatically allowlisted.",
                    matched_values=[],
                )
            )
    return triaged


def build_allowlist_policy() -> RedactionAllowlistPolicy:
    return RedactionAllowlistPolicy(
        policy_version="1",
        status="DESIGN_ONLY_NOT_APPLIED",
        allowed_classes=["ALLOWLIST_CANDIDATE_TECHNICAL_IDENTIFIER"],
        forbidden_classes=["FORBIDDEN_REQUIRES_REVIEW", "UNRESOLVED_REQUIRES_REVIEW"],
        required_review_before_submission=True,
        embedding_submission_allowed=False,
    )


def build_redaction_triage_report(*, payload_report_path: Path, request_jsonl_path: Path) -> RedactionTriageReport:
    if not payload_report_path.exists():
        raise FileNotFoundError(f"Payload report not found: {payload_report_path}")
    if not request_jsonl_path.exists():
        raise FileNotFoundError(f"Full-text request JSONL not found: {request_jsonl_path}")
    payload_report = read_json(payload_report_path)
    request_rows = read_jsonl(request_jsonl_path)
    triaged = triage_payload_findings(payload_report=payload_report, request_rows=request_rows)
    unresolved = [finding for finding in triaged if finding.classification != "ALLOWLIST_CANDIDATE_TECHNICAL_IDENTIFIER"]
    allowlisted = [finding for finding in triaged if finding.classification == "ALLOWLIST_CANDIDATE_TECHNICAL_IDENTIFIER"]
    root = repo_root()
    source_payload_report = str(payload_report_path.relative_to(root)) if payload_report_path.is_relative_to(root) else str(payload_report_path)
    source_request_jsonl = str(request_jsonl_path.relative_to(root)) if request_jsonl_path.is_relative_to(root) else str(request_jsonl_path)
    source_finding_count = int(payload_report.get("finding_count") or 0)
    status = "TRIAGE_COMPLETE_REVIEW_REQUIRED" if unresolved else "TRIAGE_COMPLETE_ALLOWLIST_CANDIDATE_ONLY"
    return RedactionTriageReport(
        report_version="1",
        status=status,
        source_payload_report=source_payload_report,
        source_request_jsonl=source_request_jsonl,
        source_finding_count=source_finding_count,
        triaged_finding_count=len(triaged),
        unresolved_finding_count=len(unresolved),
        allowlisted_finding_count=len(allowlisted),
        findings=triaged,
        allowlist_policy=build_allowlist_policy(),
        embedding_submission_allowed=False,
        vectors_created=False,
    )


def write_redaction_triage_report(path: Path, report: RedactionTriageReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build Gate 18H redaction finding triage and allowlist design report.")
    parser.add_argument("--payload-report", type=Path, default=root / DEFAULT_FULL_TEXT_PAYLOAD_REPORT)
    parser.add_argument("--request-jsonl", type=Path, default=root / DEFAULT_FULL_TEXT_REQUEST_JSONL)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_TRIAGE_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_redaction_triage_report(payload_report_path=args.payload_report, request_jsonl_path=args.request_jsonl)
    write_redaction_triage_report(args.output, report)
    print(f"[gate18h:triage] Wrote redaction triage report: {args.output}")
    print(f"[gate18h:triage] source_findings={report.source_finding_count}")
    print(f"[gate18h:triage] triaged_findings={report.triaged_finding_count}")
    print(f"[gate18h:triage] allowlist_candidates={report.allowlisted_finding_count}")
    print(f"[gate18h:triage] unresolved_findings={report.unresolved_finding_count}")
    print("[gate18h:triage] embedding_submission=forbidden")


if __name__ == "__main__":
    main()
