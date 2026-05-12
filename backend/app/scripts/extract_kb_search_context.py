from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pypdf import PdfReader

from app.scripts.extract_kb_source_manifest import relpath, repo_root

SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True)
class PageContext:
    page_number: int
    text: str
    char_count: int
    image_count: int
    highlight_annotation_count: int


@dataclass(frozen=True)
class KBSearchContextArtifact:
    artifact_type: str
    schema_version: str
    generated_utc: str
    source_lineage: dict[str, Any]
    kb_row: dict[str, Any]
    evidence_attachment: dict[str, Any]
    extraction: dict[str, Any]
    context_flags: dict[str, Any]
    content: dict[str, Any]
    pages: list[PageContext]


@dataclass(frozen=True)
class KBSearchContextManifest:
    manifest_type: str
    generated_utc: str
    evidence_map_path: str
    output_root: str
    matched_row_count: int
    artifact_count: int
    extraction_failed_count: int
    empty_text_count: int
    image_bearing_artifact_count: int
    highlight_bearing_artifact_count: int
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    failures: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_slug(value: str | None, *, fallback: str) -> str:
    raw = (value or fallback).strip() or fallback
    safe = SAFE_FILENAME_RE.sub("_", raw).strip("._")
    return safe or fallback


def normalize_text(text: str | None) -> str:
    if not text:
        return ""

    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[\t\f\v]+", " ", normalized)
    normalized = re.sub(r"[ \u00a0]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def count_page_images(page: Any) -> int:
    try:
        images = getattr(page, "images", None)
        if images is None:
            return 0
        return len(images)
    except Exception:  # noqa: BLE001 - image metadata is advisory only.
        return 0


def count_highlight_annotations(page: Any) -> int:
    try:
        annotations = page.get("/Annots") or []
        count = 0
        for annotation_ref in annotations:
            annotation = annotation_ref.get_object()
            if annotation.get("/Subtype") == "/Highlight":
                count += 1
        return count
    except Exception:  # noqa: BLE001 - annotation metadata is advisory only.
        return 0


def extract_pdf_context(pdf_path: Path) -> tuple[str, list[PageContext], dict[str, Any]]:
    reader = PdfReader(str(pdf_path))
    pages: list[PageContext] = []
    page_texts: list[str] = []

    for page_index, page in enumerate(reader.pages, start=1):
        raw_text = page.extract_text() or ""
        text = normalize_text(raw_text)
        page_texts.append(text)
        pages.append(
            PageContext(
                page_number=page_index,
                text=text,
                char_count=len(text),
                image_count=count_page_images(page),
                highlight_annotation_count=count_highlight_annotations(page),
            )
        )

    full_text = normalize_text("\n\n".join(page_texts))
    extraction = {
        "extractor": "pypdf",
        "extractor_version": "v1",
        "status": "SUCCESS",
        "page_count": len(pages),
        "char_count": len(full_text),
        "text_sha256": sha256_text(full_text),
    }
    return full_text, pages, extraction


def iter_matched_rows(evidence_map: dict[str, Any]) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    matched: list[tuple[dict[str, Any], dict[str, Any]]] = []
    for document in evidence_map.get("documents", []):
        for row in document.get("rows", []):
            if row.get("mapping_status") != "MATCHED":
                continue
            attachments = row.get("evidence_attachments") or []
            for attachment in attachments:
                matched.append((document, row | {"evidence_attachment": attachment}))
    return matched


def build_artifact(
    *,
    document: dict[str, Any],
    row: dict[str, Any],
    attachment: dict[str, Any],
    pdf_path: Path,
    repository_root: Path,
) -> KBSearchContextArtifact:
    full_text, pages, extraction = extract_pdf_context(pdf_path)
    image_count = sum(page.image_count for page in pages)
    highlight_count = sum(page.highlight_annotation_count for page in pages)

    return KBSearchContextArtifact(
        artifact_type="kb_source_search_context",
        schema_version="kb_source_search_context.v1",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        source_lineage={
            "kb_document_id": row.get("kb_document_id") or document.get("kb_document_id"),
            "source_html": row.get("source_html") or document.get("source_html"),
            "maintenance_pack": row.get("maintenance_pack") or document.get("maintenance_pack"),
            "hot_fix_release_label": row.get("hot_fix_release_label"),
            "portfolio_file": row.get("about_window_file") or attachment.get("parent_portfolio_file"),
            "child_pdf_path": relpath(pdf_path, repository_root),
            "child_sha256": attachment.get("child_sha256"),
        },
        kb_row={
            "bug_patch_number": row.get("bug_patch_number"),
            "product": row.get("product"),
            "category": row.get("category"),
            "description": row.get("description"),
            "mapping_status": row.get("mapping_status"),
        },
        evidence_attachment=attachment,
        extraction=extraction,
        context_flags={
            "has_text": bool(full_text),
            "has_images": image_count > 0,
            "image_count": image_count,
            "has_highlight_annotations": highlight_count > 0,
            "highlight_annotation_count": highlight_count,
        },
        content={
            "text": full_text,
            "char_count": len(full_text),
        },
        pages=pages,
    )


def artifact_output_path(
    *,
    artifact: KBSearchContextArtifact,
    output_root: Path,
) -> Path:
    kb_id = safe_slug(artifact.source_lineage.get("kb_document_id"), fallback="unknown_kb")
    bug_number = safe_slug(artifact.kb_row.get("bug_patch_number"), fallback="unknown_fix")
    child_hash = safe_slug((artifact.source_lineage.get("child_sha256") or "")[:12], fallback="nohash")
    portfolio = safe_slug(artifact.source_lineage.get("portfolio_file"), fallback="portfolio")
    filename = f"{kb_id}__{bug_number}__{portfolio}__{child_hash}.json"
    return output_root / kb_id / filename


def build_manifest(evidence_map_path: Path, output_root: Path) -> KBSearchContextManifest:
    repository_root = repo_root()
    evidence_map = read_json(evidence_map_path)
    matched_rows = iter_matched_rows(evidence_map)

    artifact_records: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    empty_text_count = 0
    image_bearing_count = 0
    highlight_bearing_count = 0

    for document, row in matched_rows:
        attachment = row["evidence_attachment"]
        raw_child_path = attachment.get("child_output_path")
        if not raw_child_path:
            failures.append(
                {
                    "status": "FAILED",
                    "reason": "MISSING_CHILD_OUTPUT_PATH",
                    "kb_document_id": row.get("kb_document_id"),
                    "bug_patch_number": row.get("bug_patch_number"),
                }
            )
            continue

        pdf_path = repository_root / raw_child_path
        if not pdf_path.exists():
            failures.append(
                {
                    "status": "FAILED",
                    "reason": "CHILD_PDF_NOT_FOUND",
                    "child_output_path": raw_child_path,
                    "kb_document_id": row.get("kb_document_id"),
                    "bug_patch_number": row.get("bug_patch_number"),
                }
            )
            continue

        try:
            artifact = build_artifact(
                document=document,
                row=row,
                attachment=attachment,
                pdf_path=pdf_path,
                repository_root=repository_root,
            )
        except Exception as exc:  # noqa: BLE001 - preserve per-document extraction failure.
            failures.append(
                {
                    "status": "FAILED",
                    "reason": "TEXT_EXTRACTION_FAILED",
                    "error": str(exc),
                    "child_output_path": raw_child_path,
                    "kb_document_id": row.get("kb_document_id"),
                    "bug_patch_number": row.get("bug_patch_number"),
                }
            )
            continue

        output_path = artifact_output_path(artifact=artifact, output_root=output_root)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(asdict(artifact), indent=2, sort_keys=True) + "\n", encoding="utf-8")

        if not artifact.context_flags["has_text"]:
            empty_text_count += 1
        if artifact.context_flags["has_images"]:
            image_bearing_count += 1
        if artifact.context_flags["has_highlight_annotations"]:
            highlight_bearing_count += 1

        artifact_records.append(
            {
                "artifact_path": relpath(output_path, repository_root),
                "kb_document_id": artifact.source_lineage.get("kb_document_id"),
                "maintenance_pack": artifact.source_lineage.get("maintenance_pack"),
                "portfolio_file": artifact.source_lineage.get("portfolio_file"),
                "child_pdf_path": artifact.source_lineage.get("child_pdf_path"),
                "child_sha256": artifact.source_lineage.get("child_sha256"),
                "bug_patch_number": artifact.kb_row.get("bug_patch_number"),
                "product": artifact.kb_row.get("product"),
                "category": artifact.kb_row.get("category"),
                "char_count": artifact.content["char_count"],
                "page_count": artifact.extraction["page_count"],
                "has_images": artifact.context_flags["has_images"],
                "image_count": artifact.context_flags["image_count"],
                "has_highlight_annotations": artifact.context_flags["has_highlight_annotations"],
                "highlight_annotation_count": artifact.context_flags["highlight_annotation_count"],
                "text_sha256": artifact.extraction["text_sha256"],
            }
        )

    warnings: list[str] = []
    if failures:
        warnings.append("One or more matched PFDS attachments failed text extraction.")
    if empty_text_count:
        warnings.append("One or more search context artifacts contain no extracted text.")
    if image_bearing_count:
        warnings.append("One or more search context artifacts contain image-bearing pages that may need visual review.")
    if highlight_bearing_count:
        warnings.append("One or more search context artifacts contain highlight annotations.")

    return KBSearchContextManifest(
        manifest_type="kb_search_context_manifest.v1",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        evidence_map_path=relpath(evidence_map_path, repository_root),
        output_root=relpath(output_root, repository_root),
        matched_row_count=len(matched_rows),
        artifact_count=len(artifact_records),
        extraction_failed_count=len(failures),
        empty_text_count=empty_text_count,
        image_bearing_artifact_count=image_bearing_count,
        highlight_bearing_artifact_count=highlight_bearing_count,
        artifacts=artifact_records,
        failures=failures,
        warnings=warnings,
    )


def write_manifest(manifest: KBSearchContextManifest, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Extract Gate 2 search-context artifacts from matched KB PFDS child PDFs."
    )
    parser.add_argument(
        "--evidence-map",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_evidence_map.json",
        help="Path to kb_evidence_map.json generated by Gate 1.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=root / "kbs" / "search_context",
        help="Directory where KB search-context artifacts should be written.",
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_search_context_manifest.json",
        help="Gate 2 search-context manifest output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(args.evidence_map, args.output_root)
    write_manifest(manifest, args.manifest_output)

    print(f"Wrote KB search context manifest: {args.manifest_output}")
    print(f"Matched PFDS evidence rows: {manifest.matched_row_count}")
    print(f"Search context artifacts: {manifest.artifact_count}")
    print(f"Extraction failures: {manifest.extraction_failed_count}")
    print(f"Empty text artifacts: {manifest.empty_text_count}")
    print(f"Image-bearing artifacts: {manifest.image_bearing_artifact_count}")
    print(f"Highlight-bearing artifacts: {manifest.highlight_bearing_artifact_count}")


if __name__ == "__main__":
    main()
