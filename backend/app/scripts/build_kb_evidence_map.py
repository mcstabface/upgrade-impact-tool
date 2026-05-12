from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import relpath, repo_root


@dataclass(frozen=True)
class EvidenceAttachment:
    parent_portfolio_file: str
    child_original_filename: str
    child_output_filename: str
    child_output_path: str
    child_sha256: str | None
    child_size_bytes: int | None
    candidate_fix_identifier: str | None
    candidate_fix_number: str | None
    candidate_fix_type: str | None
    attachment_classification: str | None


@dataclass(frozen=True)
class EvidenceMapRow:
    kb_document_id: str | None
    source_html: str
    maintenance_pack: str | None
    hot_fix_release_label: str | None
    about_window_file: str | None
    bug_patch_number: str | None
    product: str | None
    category: str | None
    description: str | None
    kb_extraction_status: str
    kb_extraction_warnings: list[str]
    mapping_status: str
    mapping_warnings: list[str]
    evidence_attachments: list[EvidenceAttachment] = field(default_factory=list)
    placeholder_attachments: list[EvidenceAttachment] = field(default_factory=list)


@dataclass(frozen=True)
class EvidenceMapDocument:
    kb_document_id: str | None
    source_html: str
    maintenance_pack: str | None
    fix_row_count: int
    matched_row_count: int
    placeholder_row_count: int
    missing_evidence_row_count: int
    non_joinable_row_count: int
    rows: list[EvidenceMapRow]


@dataclass(frozen=True)
class EvidenceMapManifest:
    manifest_type: str
    generated_utc: str
    kb_fix_rows_manifest_path: str
    portfolio_extraction_manifest_path: str
    document_count: int
    fix_row_count: int
    matched_row_count: int
    placeholder_row_count: int
    missing_evidence_row_count: int
    non_joinable_row_count: int
    duplicate_evidence_row_count: int
    documents: list[EvidenceMapDocument]
    warnings: list[str]


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def attachment_from_raw(raw: dict[str, Any]) -> EvidenceAttachment:
    return EvidenceAttachment(
        parent_portfolio_file=raw.get("parent_portfolio_file"),
        child_original_filename=raw.get("child_original_filename"),
        child_output_filename=raw.get("child_output_filename"),
        child_output_path=raw.get("child_output_path"),
        child_sha256=raw.get("child_sha256"),
        child_size_bytes=raw.get("child_size_bytes"),
        candidate_fix_identifier=raw.get("candidate_fix_identifier"),
        candidate_fix_number=raw.get("candidate_fix_number"),
        candidate_fix_type=raw.get("candidate_fix_type"),
        attachment_classification=raw.get("attachment_classification"),
    )


def placeholder_from_raw(raw: dict[str, Any]) -> EvidenceAttachment:
    return EvidenceAttachment(
        parent_portfolio_file=raw.get("parent_portfolio_file"),
        child_original_filename=raw.get("child_original_filename"),
        child_output_filename=raw.get("child_output_filename"),
        child_output_path=raw.get("child_output_path"),
        child_sha256=raw.get("child_sha256"),
        child_size_bytes=raw.get("child_size_bytes"),
        candidate_fix_identifier=raw.get("candidate_fix_identifier"),
        candidate_fix_number=raw.get("candidate_fix_number"),
        candidate_fix_type=raw.get("candidate_fix_type"),
        attachment_classification=raw.get("classification") or raw.get("attachment_classification"),
    )


def build_attachment_index(portfolio_manifest: dict[str, Any]) -> tuple[dict[tuple[str, str], list[EvidenceAttachment]], dict[str, list[EvidenceAttachment]]]:
    by_portfolio_and_fix: dict[tuple[str, str], list[EvidenceAttachment]] = {}
    placeholders_by_portfolio: dict[str, list[EvidenceAttachment]] = {}

    for portfolio in portfolio_manifest.get("portfolios", []):
        parent_file = portfolio.get("parent_portfolio_file")
        if not parent_file:
            continue

        for raw_attachment in portfolio.get("extracted_attachments", []):
            attachment = attachment_from_raw(raw_attachment)
            if attachment.candidate_fix_number:
                key = (parent_file, attachment.candidate_fix_number)
                by_portfolio_and_fix.setdefault(key, []).append(attachment)

        for raw_placeholder in portfolio.get("placeholder_attachments", []):
            placeholder = placeholder_from_raw(raw_placeholder)
            placeholders_by_portfolio.setdefault(parent_file, []).append(placeholder)

    return by_portfolio_and_fix, placeholders_by_portfolio


def map_row(
    raw_row: dict[str, Any],
    *,
    attachment_index: dict[tuple[str, str], list[EvidenceAttachment]],
    placeholders_by_portfolio: dict[str, list[EvidenceAttachment]],
) -> EvidenceMapRow:
    about_window_file = raw_row.get("about_window_file")
    bug_patch_number = raw_row.get("bug_patch_number")
    warnings: list[str] = []

    if not about_window_file:
        warnings.append("KB row has no About Window / portfolio reference.")
        status = "ROW_MISSING_PORTFOLIO_REFERENCE"
        evidence: list[EvidenceAttachment] = []
        placeholders: list[EvidenceAttachment] = []
    elif not bug_patch_number:
        placeholders = placeholders_by_portfolio.get(about_window_file, [])
        if placeholders:
            status = "PORTFOLIO_PLACEHOLDER_NO_PFDS"
        else:
            status = "ROW_MISSING_FIX_IDENTIFIER"
            warnings.append("KB row has no bug / patch identifier to join against extracted source attachments.")
        evidence = []
    else:
        evidence = attachment_index.get((about_window_file, bug_patch_number), [])
        placeholders = placeholders_by_portfolio.get(about_window_file, [])
        if len(evidence) == 1:
            status = "MATCHED"
        elif len(evidence) > 1:
            status = "MULTIPLE_EVIDENCE_CANDIDATES"
            warnings.append("More than one extracted attachment matched this KB row.")
        elif placeholders:
            status = "PORTFOLIO_PLACEHOLDER_NO_PFDS"
            warnings.append("Portfolio contains a no-PFDS placeholder and no matching attachment for this KB row.")
        else:
            status = "NO_EVIDENCE_ATTACHMENT_FOUND"
            warnings.append("No extracted attachment matched the KB row bug / patch number within the referenced portfolio.")

    return EvidenceMapRow(
        kb_document_id=raw_row.get("kb_document_id"),
        source_html=raw_row.get("source_html"),
        maintenance_pack=raw_row.get("maintenance_pack"),
        hot_fix_release_label=raw_row.get("hot_fix_release_label"),
        about_window_file=about_window_file,
        bug_patch_number=bug_patch_number,
        product=raw_row.get("product"),
        category=raw_row.get("category"),
        description=raw_row.get("description"),
        kb_extraction_status=raw_row.get("extraction_status"),
        kb_extraction_warnings=raw_row.get("extraction_warnings", []),
        mapping_status=status,
        mapping_warnings=warnings,
        evidence_attachments=evidence,
        placeholder_attachments=placeholders,
    )


def document_counts(rows: list[EvidenceMapRow]) -> dict[str, int]:
    return {
        "matched_row_count": sum(1 for row in rows if row.mapping_status == "MATCHED"),
        "placeholder_row_count": sum(1 for row in rows if row.mapping_status == "PORTFOLIO_PLACEHOLDER_NO_PFDS"),
        "missing_evidence_row_count": sum(1 for row in rows if row.mapping_status == "NO_EVIDENCE_ATTACHMENT_FOUND"),
        "non_joinable_row_count": sum(
            1
            for row in rows
            if row.mapping_status in {"ROW_MISSING_FIX_IDENTIFIER", "ROW_MISSING_PORTFOLIO_REFERENCE"}
        ),
        "duplicate_evidence_row_count": sum(1 for row in rows if row.mapping_status == "MULTIPLE_EVIDENCE_CANDIDATES"),
    }


def build_manifest(kb_fix_rows_path: Path, portfolio_extraction_path: Path) -> EvidenceMapManifest:
    repository_root = repo_root()
    kb_manifest = read_json(kb_fix_rows_path)
    portfolio_manifest = read_json(portfolio_extraction_path)
    attachment_index, placeholders_by_portfolio = build_attachment_index(portfolio_manifest)

    documents: list[EvidenceMapDocument] = []
    for raw_document in kb_manifest.get("documents", []):
        rows = [
            map_row(
                raw_row,
                attachment_index=attachment_index,
                placeholders_by_portfolio=placeholders_by_portfolio,
            )
            for raw_row in raw_document.get("fix_rows", [])
        ]
        counts = document_counts(rows)
        documents.append(
            EvidenceMapDocument(
                kb_document_id=raw_document.get("kb_document_id"),
                source_html=raw_document.get("source_html"),
                maintenance_pack=raw_document.get("maintenance_pack"),
                fix_row_count=len(rows),
                matched_row_count=counts["matched_row_count"],
                placeholder_row_count=counts["placeholder_row_count"],
                missing_evidence_row_count=counts["missing_evidence_row_count"],
                non_joinable_row_count=counts["non_joinable_row_count"],
                rows=rows,
            )
        )

    all_rows = [row for document in documents for row in document.rows]
    all_counts = document_counts(all_rows)
    warnings: list[str] = []
    if all_counts["missing_evidence_row_count"]:
        warnings.append("One or more KB rows did not match an extracted PFDS attachment.")
    if all_counts["non_joinable_row_count"]:
        warnings.append("One or more KB rows could not be joined because they lack a fix identifier or portfolio reference.")

    return EvidenceMapManifest(
        manifest_type="kb_evidence_map.v1",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        kb_fix_rows_manifest_path=relpath(kb_fix_rows_path, repository_root),
        portfolio_extraction_manifest_path=relpath(portfolio_extraction_path, repository_root),
        document_count=len(documents),
        fix_row_count=len(all_rows),
        matched_row_count=all_counts["matched_row_count"],
        placeholder_row_count=all_counts["placeholder_row_count"],
        missing_evidence_row_count=all_counts["missing_evidence_row_count"],
        non_joinable_row_count=all_counts["non_joinable_row_count"],
        duplicate_evidence_row_count=all_counts["duplicate_evidence_row_count"],
        documents=documents,
        warnings=warnings,
    )


def write_manifest(manifest: EvidenceMapManifest, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Join KB fix rows to extracted portfolio PFDS attachments."
    )
    parser.add_argument(
        "--kb-fix-rows",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_fix_rows.json",
        help="Path to kb_fix_rows.json.",
    )
    parser.add_argument(
        "--portfolio-extraction",
        type=Path,
        default=root / "kbs" / "manifests" / "portfolio_extraction.json",
        help="Path to portfolio_extraction.json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_evidence_map.json",
        help="Evidence map manifest output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_manifest(args.kb_fix_rows, args.portfolio_extraction)
    write_manifest(manifest, args.output)

    print(f"Wrote KB evidence map manifest: {args.output}")
    print(f"Documents: {manifest.document_count}")
    print(f"Fix rows: {manifest.fix_row_count}")
    print(f"Matched rows: {manifest.matched_row_count}")
    print(f"Placeholder rows: {manifest.placeholder_row_count}")
    print(f"Missing evidence rows: {manifest.missing_evidence_row_count}")
    print(f"Non-joinable rows: {manifest.non_joinable_row_count}")
    print(f"Duplicate evidence rows: {manifest.duplicate_evidence_row_count}")


if __name__ == "__main__":
    main()
