from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


@dataclass(frozen=True)
class KBSummary:
    kb_document_id: str
    text_artifact_count: int
    chunk_collection_count: int
    chunk_count: int
    image_bearing_artifact_count: int
    highlight_bearing_artifact_count: int
    empty_text_count: int


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def value_or_unknown(value: Any) -> str:
    if value is None:
        return "UNKNOWN"
    text = str(value).strip()
    return text or "UNKNOWN"


def markdown_escape(value: Any) -> str:
    text = value_or_unknown(value)
    return text.replace("|", "\\|").replace("\n", " ")


def build_per_kb_summary(text_manifest: dict[str, Any], chunk_manifest: dict[str, Any]) -> list[KBSummary]:
    text_by_kb: Counter[str] = Counter()
    image_by_kb: Counter[str] = Counter()
    highlight_by_kb: Counter[str] = Counter()
    empty_by_kb: Counter[str] = Counter()

    for artifact in text_manifest.get("artifacts", []):
        kb_id = value_or_unknown(artifact.get("kb_document_id"))
        text_by_kb[kb_id] += 1
        if artifact.get("has_images"):
            image_by_kb[kb_id] += 1
        if artifact.get("has_highlight_annotations"):
            highlight_by_kb[kb_id] += 1
        if artifact.get("char_count", 0) == 0:
            empty_by_kb[kb_id] += 1

    collections_by_kb: Counter[str] = Counter()
    chunks_by_kb: Counter[str] = Counter()
    for collection in chunk_manifest.get("collections", []):
        kb_id = value_or_unknown(collection.get("kb_document_id"))
        collections_by_kb[kb_id] += 1
        chunks_by_kb[kb_id] += int(collection.get("chunk_count") or 0)

    all_kbs = sorted(set(text_by_kb) | set(collections_by_kb))
    return [
        KBSummary(
            kb_document_id=kb_id,
            text_artifact_count=text_by_kb[kb_id],
            chunk_collection_count=collections_by_kb[kb_id],
            chunk_count=chunks_by_kb[kb_id],
            image_bearing_artifact_count=image_by_kb[kb_id],
            highlight_bearing_artifact_count=highlight_by_kb[kb_id],
            empty_text_count=empty_by_kb[kb_id],
        )
        for kb_id in all_kbs
    ]


def top_image_heavy_artifacts(text_manifest: dict[str, Any], *, limit: int = 10) -> list[dict[str, Any]]:
    artifacts = [artifact for artifact in text_manifest.get("artifacts", []) if artifact.get("image_count", 0) > 0]
    return sorted(
        artifacts,
        key=lambda artifact: (
            int(artifact.get("image_count") or 0),
            int(artifact.get("page_count") or 0),
            value_or_unknown(artifact.get("kb_document_id")),
            value_or_unknown(artifact.get("bug_patch_number")),
        ),
        reverse=True,
    )[:limit]


def top_largest_chunk_collections(chunk_manifest: dict[str, Any], *, limit: int = 10) -> list[dict[str, Any]]:
    collections = list(chunk_manifest.get("collections", []))
    return sorted(
        collections,
        key=lambda collection: (
            int(collection.get("chunk_count") or 0),
            int(collection.get("source_char_count") or 0),
            value_or_unknown(collection.get("kb_document_id")),
            value_or_unknown(collection.get("bug_patch_number")),
        ),
        reverse=True,
    )[:limit]


def build_product_breakdown(text_manifest: dict[str, Any]) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for artifact in text_manifest.get("artifacts", []):
        counts[value_or_unknown(artifact.get("product"))] += 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def build_category_breakdown(text_manifest: dict[str, Any]) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for artifact in text_manifest.get("artifacts", []):
        counts[value_or_unknown(artifact.get("category"))] += 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def render_summary(text_manifest: dict[str, Any], chunk_manifest: dict[str, Any]) -> str:
    generated_utc = datetime.now(timezone.utc).isoformat()
    per_kb = build_per_kb_summary(text_manifest, chunk_manifest)
    top_images = top_image_heavy_artifacts(text_manifest)
    top_chunks = top_largest_chunk_collections(chunk_manifest)
    product_breakdown = build_product_breakdown(text_manifest)
    category_breakdown = build_category_breakdown(text_manifest)

    lines: list[str] = []
    lines.append("# KB Search Context Summary")
    lines.append("")
    lines.append(f"Generated UTC: `{generated_utc}`")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Matched PFDS evidence rows: {text_manifest.get('matched_row_count', 0)}")
    lines.append(f"- Search-context artifacts: {text_manifest.get('artifact_count', 0)}")
    lines.append(f"- Text extraction failures: {text_manifest.get('extraction_failed_count', 0)}")
    lines.append(f"- Empty-text artifacts: {text_manifest.get('empty_text_count', 0)}")
    lines.append(f"- Image-bearing artifacts: {text_manifest.get('image_bearing_artifact_count', 0)}")
    lines.append(f"- Highlight-bearing artifacts: {text_manifest.get('highlight_bearing_artifact_count', 0)}")
    lines.append(f"- Chunk collections: {chunk_manifest.get('chunk_collection_count', 0)}")
    lines.append(f"- Chunks: {chunk_manifest.get('chunk_count', 0)}")
    lines.append(f"- Chunking skipped empty-text artifacts: {chunk_manifest.get('skipped_empty_text_count', 0)}")
    lines.append(f"- Chunking failures: {chunk_manifest.get('failure_count', 0)}")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "Gate 2 materializes matched PFDS evidence into retrieval-ready source context and deterministic chunks. "
        "This is still source preparation, not upgrade impact analysis. The artifacts preserve KB and PFDS lineage so later retrieval, review, and analysis can point back to source evidence."
    )
    lines.append("")
    lines.append(
        "Image-bearing artifacts indicate PFDS documents whose extracted text may not capture all visual information. "
        "These should remain visible for reviewer awareness before relying on text-only retrieval."
    )
    lines.append("")

    lines.append("## Per-KB Breakdown")
    lines.append("")
    lines.append("| KB | Text Artifacts | Chunk Collections | Chunks | Image-Bearing | Highlights | Empty Text |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|")
    for item in per_kb:
        lines.append(
            "| "
            f"{markdown_escape(item.kb_document_id)} | "
            f"{item.text_artifact_count} | "
            f"{item.chunk_collection_count} | "
            f"{item.chunk_count} | "
            f"{item.image_bearing_artifact_count} | "
            f"{item.highlight_bearing_artifact_count} | "
            f"{item.empty_text_count} |"
        )
    lines.append("")

    lines.append("## Product Breakdown")
    lines.append("")
    lines.append("| Product | Search-Context Artifacts |")
    lines.append("|---|---:|")
    for product, count in product_breakdown:
        lines.append(f"| {markdown_escape(product)} | {count} |")
    lines.append("")

    lines.append("## Category Breakdown")
    lines.append("")
    lines.append("| Category | Search-Context Artifacts |")
    lines.append("|---|---:|")
    for category, count in category_breakdown:
        lines.append(f"| {markdown_escape(category)} | {count} |")
    lines.append("")

    lines.append("## Top Image-Heavy PFDS Artifacts")
    lines.append("")
    if top_images:
        lines.append("| KB | Bug / Patch | Product | Category | Images | Pages | Child PDF |")
        lines.append("|---|---|---|---|---:|---:|---|")
        for artifact in top_images:
            lines.append(
                "| "
                f"{markdown_escape(artifact.get('kb_document_id'))} | "
                f"{markdown_escape(artifact.get('bug_patch_number'))} | "
                f"{markdown_escape(artifact.get('product'))} | "
                f"{markdown_escape(artifact.get('category'))} | "
                f"{artifact.get('image_count', 0)} | "
                f"{artifact.get('page_count', 0)} | "
                f"`{markdown_escape(artifact.get('child_pdf_path'))}` |"
            )
    else:
        lines.append("No image-bearing PFDS artifacts were reported.")
    lines.append("")

    lines.append("## Largest Chunk Collections")
    lines.append("")
    if top_chunks:
        lines.append("| KB | Bug / Patch | Product | Category | Chunks | Source Chars | Collection |")
        lines.append("|---|---|---|---|---:|---:|---|")
        for collection in top_chunks:
            lines.append(
                "| "
                f"{markdown_escape(collection.get('kb_document_id'))} | "
                f"{markdown_escape(collection.get('bug_patch_number'))} | "
                f"{markdown_escape(collection.get('product'))} | "
                f"{markdown_escape(collection.get('category'))} | "
                f"{collection.get('chunk_count', 0)} | "
                f"{collection.get('source_char_count', 0)} | "
                f"`{markdown_escape(collection.get('collection_path'))}` |"
            )
    else:
        lines.append("No chunk collections were reported.")
    lines.append("")

    lines.append("## Manifest Inputs")
    lines.append("")
    lines.append(f"- Text manifest: `{text_manifest.get('evidence_map_path', 'kbs/manifests/kb_search_context_manifest.json')}`")
    lines.append(f"- Chunk source manifest: `{chunk_manifest.get('source_manifest_path', 'kbs/manifests/kb_search_context_manifest.json')}`")
    lines.append(f"- Chunk output root: `{chunk_manifest.get('output_root', 'kbs/search_context_chunks')}`")
    lines.append("")

    text_warnings = text_manifest.get("warnings") or []
    chunk_warnings = chunk_manifest.get("warnings") or []
    if text_warnings or chunk_warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in text_warnings:
            lines.append(f"- Text extraction: {warning}")
        for warning in chunk_warnings:
            lines.append(f"- Chunking: {warning}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Write a reviewer-facing Gate 2 KB search-context Markdown summary."
    )
    parser.add_argument(
        "--text-manifest",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_search_context_manifest.json",
        help="Path to kb_search_context_manifest.json.",
    )
    parser.add_argument(
        "--chunk-manifest",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_search_context_chunks_manifest.json",
        help="Path to kb_search_context_chunks_manifest.json.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_search_context_summary.md",
        help="Markdown summary output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    text_manifest = read_json(args.text_manifest)
    chunk_manifest = read_json(args.chunk_manifest)
    summary = render_summary(text_manifest, chunk_manifest)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(summary, encoding="utf-8")

    print(f"Wrote KB search context summary: {args.output}")
    print(f"Search-context artifacts: {text_manifest.get('artifact_count', 0)}")
    print(f"Chunk collections: {chunk_manifest.get('chunk_collection_count', 0)}")
    print(f"Chunks: {chunk_manifest.get('chunk_count', 0)}")


if __name__ == "__main__":
    main()
