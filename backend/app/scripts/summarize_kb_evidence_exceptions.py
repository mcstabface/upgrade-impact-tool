from __future__ import annotations

import argparse
import json
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import relpath, repo_root

REVIEW_STATUSES = {
    "MULTIPLE_EVIDENCE_CANDIDATES",
    "NO_EVIDENCE_ATTACHMENT_FOUND",
    "PORTFOLIO_PLACEHOLDER_NO_PFDS",
    "KB_DECLARED_NO_PFD",
    "ROW_MISSING_FIX_IDENTIFIER",
    "ROW_MISSING_PORTFOLIO_REFERENCE",
}


@dataclass(frozen=True)
class EvidenceExceptionRow:
    mapping_status: str
    severity: str
    kb_document_id: str | None
    maintenance_pack: str | None
    hot_fix_release_label: str | None
    about_window_file: str | None
    bug_patch_number: str | None
    product: str | None
    category: str | None
    description: str | None
    source_html: str | None
    mapping_warnings: list[str]
    kb_extraction_warnings: list[str]
    evidence_attachment_count: int
    placeholder_attachment_count: int
    evidence_attachment_paths: list[str] = field(default_factory=list)
    placeholder_attachment_paths: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class EvidenceExceptionDocument:
    kb_document_id: str | None
    source_html: str | None
    maintenance_pack: str | None
    exception_count: int
    status_counts: dict[str, int]
    exceptions: list[EvidenceExceptionRow]


@dataclass(frozen=True)
class EvidenceExceptionSummary:
    manifest_type: str
    generated_utc: str
    evidence_map_manifest_path: str
    document_count: int
    exception_count: int
    severity_counts: dict[str, int]
    status_counts: dict[str, int]
    documents: list[EvidenceExceptionDocument]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def classify_severity(mapping_status: str) -> str:
    if mapping_status == "NO_EVIDENCE_ATTACHMENT_FOUND":
        return "HIGH"
    if mapping_status == "MULTIPLE_EVIDENCE_CANDIDATES":
        return "MEDIUM"
    if mapping_status in {"ROW_MISSING_FIX_IDENTIFIER", "ROW_MISSING_PORTFOLIO_REFERENCE"}:
        return "MEDIUM"
    if mapping_status in {"PORTFOLIO_PLACEHOLDER_NO_PFDS", "KB_DECLARED_NO_PFD"}:
        return "LOW"
    return "LOW"


def attachment_paths(row: dict[str, Any], key: str) -> list[str]:
    paths: list[str] = []
    for attachment in row.get(key, []):
        path = attachment.get("child_output_path")
        if path:
            paths.append(path)
    return paths


def is_exception_row(row: dict[str, Any]) -> bool:
    return row.get("mapping_status") in REVIEW_STATUSES


def build_exception_row(row: dict[str, Any]) -> EvidenceExceptionRow:
    evidence_paths = attachment_paths(row, "evidence_attachments")
    placeholder_paths = attachment_paths(row, "placeholder_attachments")
    mapping_status = row.get("mapping_status") or "UNKNOWN"

    return EvidenceExceptionRow(
        mapping_status=mapping_status,
        severity=classify_severity(mapping_status),
        kb_document_id=row.get("kb_document_id"),
        maintenance_pack=row.get("maintenance_pack"),
        hot_fix_release_label=row.get("hot_fix_release_label"),
        about_window_file=row.get("about_window_file"),
        bug_patch_number=row.get("bug_patch_number"),
        product=row.get("product"),
        category=row.get("category"),
        description=row.get("description"),
        source_html=row.get("source_html"),
        mapping_warnings=row.get("mapping_warnings", []),
        kb_extraction_warnings=row.get("kb_extraction_warnings", []),
        evidence_attachment_count=len(row.get("evidence_attachments", [])),
        placeholder_attachment_count=len(row.get("placeholder_attachments", [])),
        evidence_attachment_paths=evidence_paths,
        placeholder_attachment_paths=placeholder_paths,
    )


def build_summary(evidence_map_path: Path) -> EvidenceExceptionSummary:
    repository_root = repo_root()
    evidence_map = read_json(evidence_map_path)

    documents: list[EvidenceExceptionDocument] = []
    all_exceptions: list[EvidenceExceptionRow] = []

    for raw_document in evidence_map.get("documents", []):
        exceptions = [
            build_exception_row(row)
            for row in raw_document.get("rows", [])
            if is_exception_row(row)
        ]
        if not exceptions:
            continue

        status_counts = Counter(row.mapping_status for row in exceptions)
        documents.append(
            EvidenceExceptionDocument(
                kb_document_id=raw_document.get("kb_document_id"),
                source_html=raw_document.get("source_html"),
                maintenance_pack=raw_document.get("maintenance_pack"),
                exception_count=len(exceptions),
                status_counts=dict(sorted(status_counts.items())),
                exceptions=exceptions,
            )
        )
        all_exceptions.extend(exceptions)

    severity_counts = Counter(row.severity for row in all_exceptions)
    status_counts = Counter(row.mapping_status for row in all_exceptions)

    return EvidenceExceptionSummary(
        manifest_type="kb_evidence_exceptions.v1",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        evidence_map_manifest_path=relpath(evidence_map_path, repository_root),
        document_count=len(documents),
        exception_count=len(all_exceptions),
        severity_counts=dict(sorted(severity_counts.items())),
        status_counts=dict(sorted(status_counts.items())),
        documents=documents,
    )


def write_summary(summary: EvidenceExceptionSummary, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(asdict(summary), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Create a reviewer-facing exception summary from the KB evidence map."
    )
    parser.add_argument(
        "--evidence-map",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_evidence_map.json",
        help="Path to kb_evidence_map.json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_evidence_exceptions.json",
        help="Exception summary output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = build_summary(args.evidence_map)
    write_summary(summary, args.output)

    print(f"Wrote KB evidence exception summary: {args.output}")
    print(f"Documents with exceptions: {summary.document_count}")
    print(f"Exceptions: {summary.exception_count}")
    print(f"Severity counts: {summary.severity_counts}")
    print(f"Status counts: {summary.status_counts}")


if __name__ == "__main__":
    main()
