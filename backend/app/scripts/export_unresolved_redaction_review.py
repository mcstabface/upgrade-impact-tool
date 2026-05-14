from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_TRIAGE_REPORT = "kbs/retrieval/kb_embedding_redaction_triage_report.v1.json"
DEFAULT_REQUEST_JSONL = "kbs/retrieval/kb_embedding_full_text_requests.v1.jsonl"
DEFAULT_REVIEW_EXPORT_JSON = "kbs/retrieval/kb_embedding_unresolved_redaction_review.v1.json"
DEFAULT_REVIEW_EXPORT_MD = "kbs/retrieval/kb_embedding_unresolved_redaction_review.v1.md"

UNRESOLVED_CLASSES = {"UNRESOLVED_REQUIRES_REVIEW", "FORBIDDEN_REQUIRES_REVIEW"}


@dataclass(frozen=True)
class UnresolvedRedactionReviewItem:
    review_id: str
    chunk_id: str
    code: str
    classification: str
    matched_values: list[str]
    context_window: str
    citation_payload: dict[str, Any] = field(default_factory=dict)
    reviewer_decision: str = "PENDING"
    reviewer_notes: str = ""


@dataclass(frozen=True)
class UnresolvedRedactionReviewExport:
    export_version: str
    status: str
    source_triage_report: str
    source_request_jsonl: str
    unresolved_count: int
    items: list[UnresolvedRedactionReviewItem]
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


def request_rows_by_chunk_id(request_rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_chunk_id: dict[str, dict[str, Any]] = {}
    for row in request_rows:
        chunk_id = str(row.get("chunk_id") or "")
        if not chunk_id:
            raise ValueError("Request row missing chunk_id")
        if chunk_id in by_chunk_id:
            raise ValueError(f"Duplicate request row chunk_id: {chunk_id}")
        by_chunk_id[chunk_id] = row
    return by_chunk_id


def context_for_values(text: str, values: list[str], *, radius: int = 120) -> str:
    if not values:
        return text[: radius * 2].replace("\n", " ").strip()
    first_value = values[0]
    index = text.find(first_value)
    if index < 0:
        return text[: radius * 2].replace("\n", " ").strip()
    start = max(0, index - radius)
    end = min(len(text), index + len(first_value) + radius)
    return text[start:end].replace("\n", " ").strip()


def build_review_export(*, triage_report_path: Path, request_jsonl_path: Path) -> UnresolvedRedactionReviewExport:
    if not triage_report_path.exists():
        raise FileNotFoundError(f"Triage report not found: {triage_report_path}")
    if not request_jsonl_path.exists():
        raise FileNotFoundError(f"Full-text request JSONL not found: {request_jsonl_path}")
    triage_report = read_json(triage_report_path)
    findings = triage_report.get("findings")
    if not isinstance(findings, list):
        raise ValueError("Triage report findings must be a list")
    request_rows = request_rows_by_chunk_id(read_jsonl(request_jsonl_path))

    items: list[UnresolvedRedactionReviewItem] = []
    for index, finding in enumerate(findings, start=1):
        if not isinstance(finding, dict):
            raise ValueError("Triage finding must be an object")
        classification = str(finding.get("classification") or "")
        if classification not in UNRESOLVED_CLASSES:
            continue
        chunk_id = str(finding.get("chunk_id") or "")
        request_row = request_rows.get(chunk_id)
        if request_row is None:
            raise ValueError(f"No request row found for unresolved chunk: {chunk_id}")
        matched_values = finding.get("matched_values") or []
        if not isinstance(matched_values, list):
            raise ValueError(f"matched_values must be a list for chunk: {chunk_id}")
        input_text = str(request_row.get("input_text") or "")
        citation_payload = request_row.get("citation_payload") or {}
        if not isinstance(citation_payload, dict):
            raise ValueError(f"citation_payload must be object for chunk: {chunk_id}")
        items.append(
            UnresolvedRedactionReviewItem(
                review_id=f"redaction-review-{index:04d}",
                chunk_id=chunk_id,
                code=str(finding.get("code") or ""),
                classification=classification,
                matched_values=[str(value) for value in matched_values],
                context_window=context_for_values(input_text, [str(value) for value in matched_values]),
                citation_payload=citation_payload,
            )
        )

    root = repo_root()
    source_triage_report = str(triage_report_path.relative_to(root)) if triage_report_path.is_relative_to(root) else str(triage_report_path)
    source_request_jsonl = str(request_jsonl_path.relative_to(root)) if request_jsonl_path.is_relative_to(root) else str(request_jsonl_path)
    return UnresolvedRedactionReviewExport(
        export_version="1",
        status="REVIEW_REQUIRED" if items else "NO_UNRESOLVED_FINDINGS",
        source_triage_report=source_triage_report,
        source_request_jsonl=source_request_jsonl,
        unresolved_count=len(items),
        items=items,
        embedding_submission_allowed=False,
        vectors_created=False,
    )


def write_review_export_json(path: Path, export: UnresolvedRedactionReviewExport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(export), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def markdown_escape(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", " ")


def write_review_export_markdown(path: Path, export: UnresolvedRedactionReviewExport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Gate 18J Unresolved Redaction Review Export",
        "",
        f"Status: {export.status}",
        f"Unresolved findings: {export.unresolved_count}",
        "Embedding submission allowed: false",
        "Vectors created: false",
        "",
        "| Review ID | Code | Classification | Matched Values | Context | Decision | Notes |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in export.items:
        lines.append(
            "| "
            + " | ".join(
                [
                    markdown_escape(item.review_id),
                    markdown_escape(item.code),
                    markdown_escape(item.classification),
                    markdown_escape(", ".join(item.matched_values)),
                    markdown_escape(item.context_window),
                    markdown_escape(item.reviewer_decision),
                    markdown_escape(item.reviewer_notes),
                ]
            )
            + " |"
        )
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Export Gate 18J unresolved redaction findings for review.")
    parser.add_argument("--triage-report", type=Path, default=root / DEFAULT_TRIAGE_REPORT)
    parser.add_argument("--request-jsonl", type=Path, default=root / DEFAULT_REQUEST_JSONL)
    parser.add_argument("--json-output", type=Path, default=root / DEFAULT_REVIEW_EXPORT_JSON)
    parser.add_argument("--markdown-output", type=Path, default=root / DEFAULT_REVIEW_EXPORT_MD)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    export = build_review_export(triage_report_path=args.triage_report, request_jsonl_path=args.request_jsonl)
    write_review_export_json(args.json_output, export)
    write_review_export_markdown(args.markdown_output, export)
    print(f"[gate18j:review] Wrote unresolved redaction review JSON: {args.json_output}")
    print(f"[gate18j:review] Wrote unresolved redaction review Markdown: {args.markdown_output}")
    print(f"[gate18j:review] unresolved_findings={export.unresolved_count}")
    print("[gate18j:review] embedding_submission=forbidden")
    print("[gate18j:review] vectors=not_created")


if __name__ == "__main__":
    main()
