from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def value_or_unknown(value: Any) -> str:
    if value is None:
        return "UNKNOWN"
    text = str(value).strip()
    return text or "UNKNOWN"


def markdown_escape(value: Any) -> str:
    return value_or_unknown(value).replace("|", "\\|").replace("\n", " ")


def latest_query_context(query_context_root: Path) -> tuple[Path | None, dict[str, Any] | None]:
    if not query_context_root.exists():
        return None, None
    artifacts = sorted(query_context_root.glob("*.query_context.json"))
    if not artifacts:
        return None, None
    latest = max(artifacts, key=lambda path: path.stat().st_mtime)
    return latest, read_json(latest)


def per_kb_counts(collections: list[dict[str, Any]]) -> list[tuple[str, int, int, int]]:
    collection_count: Counter[str] = Counter()
    chunk_count: Counter[str] = Counter()
    token_count: Counter[str] = Counter()
    for collection in collections:
        kb_id = value_or_unknown(collection.get("kb_document_id"))
        collection_count[kb_id] += 1
        chunk_count[kb_id] += int(collection.get("indexed_chunk_count") or 0)
        token_count[kb_id] += int(collection.get("token_count") or 0)
    return sorted(
        [(kb_id, collection_count[kb_id], chunk_count[kb_id], token_count[kb_id]) for kb_id in collection_count],
        key=lambda item: item[0],
    )


def product_counts(collections: list[dict[str, Any]]) -> list[tuple[str, int, int]]:
    collection_count: Counter[str] = Counter()
    chunk_count: Counter[str] = Counter()
    for collection in collections:
        product = value_or_unknown(collection.get("product"))
        collection_count[product] += 1
        chunk_count[product] += int(collection.get("indexed_chunk_count") or 0)
    return sorted(
        [(product, collection_count[product], chunk_count[product]) for product in collection_count],
        key=lambda item: (-item[1], item[0]),
    )


def category_counts(collections: list[dict[str, Any]]) -> list[tuple[str, int, int]]:
    collection_count: Counter[str] = Counter()
    chunk_count: Counter[str] = Counter()
    for collection in collections:
        category = value_or_unknown(collection.get("category"))
        collection_count[category] += 1
        chunk_count[category] += int(collection.get("indexed_chunk_count") or 0)
    return sorted(
        [(category, collection_count[category], chunk_count[category]) for category in collection_count],
        key=lambda item: (-item[1], item[0]),
    )


def top_token_heavy_collections(collections: list[dict[str, Any]], *, limit: int = 10) -> list[dict[str, Any]]:
    return sorted(
        collections,
        key=lambda item: (
            int(item.get("token_count") or 0),
            int(item.get("indexed_chunk_count") or 0),
            value_or_unknown(item.get("kb_document_id")),
            value_or_unknown(item.get("bug_patch_number")),
        ),
        reverse=True,
    )[:limit]


def render_query_section(query_context_path: Path | None, query_context: dict[str, Any] | None) -> list[str]:
    lines: list[str] = []
    lines.append("## Latest Smoke Query")
    lines.append("")
    if not query_context_path or not query_context:
        lines.append("No query context artifact was found.")
        lines.append("")
        return lines

    query = query_context.get("query", {})
    diagnostics = query_context.get("diagnostics", {})
    lines.append(f"- Query artifact: `{query_context_path.as_posix()}`")
    lines.append(f"- Query text: `{query.get('query_text', '')}`")
    lines.append(f"- Query terms: `{', '.join(query.get('query_terms', []))}`")
    lines.append(f"- Candidate chunks: {diagnostics.get('candidate_count', 0)}")
    lines.append(f"- Scored chunks: {diagnostics.get('scored_count', 0)}")
    lines.append(f"- Returned chunks: {diagnostics.get('returned_count', 0)}")
    lines.append(f"- Ranker: `{diagnostics.get('ranker', 'UNKNOWN')}`")
    lines.append("")

    results = query_context.get("results", [])
    if results:
        lines.append("| Rank | Score | KB | Bug / Patch | Product | Category | Matched Terms |")
        lines.append("|---:|---:|---|---|---|---|---|")
        for result in results[:10]:
            lines.append(
                "| "
                f"{result.get('rank', '')} | "
                f"{result.get('score', '')} | "
                f"{markdown_escape(result.get('kb_document_id'))} | "
                f"{markdown_escape(result.get('bug_patch_number'))} | "
                f"{markdown_escape(result.get('product'))} | "
                f"{markdown_escape(result.get('category'))} | "
                f"{markdown_escape(', '.join(result.get('matched_terms', [])))} |"
            )
        lines.append("")
    return lines


def render_summary(index_manifest: dict[str, Any], query_context_root: Path) -> str:
    generated_utc = datetime.now(timezone.utc).isoformat()
    collections = index_manifest.get("collections", [])
    latest_path, latest_context = latest_query_context(query_context_root)

    lines: list[str] = []
    lines.append("# KB PFDS Retrieval Summary")
    lines.append("")
    lines.append(f"Generated UTC: `{generated_utc}`")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Source chunk collections: {index_manifest.get('collection_count', 0)}")
    lines.append(f"- Indexed collections: {index_manifest.get('indexed_collection_count', 0)}")
    lines.append(f"- Source chunks: {index_manifest.get('chunk_count', 0)}")
    lines.append(f"- Indexed chunks: {index_manifest.get('indexed_chunk_count', 0)}")
    lines.append(f"- Posting rows: {index_manifest.get('posting_count', 0)}")
    lines.append(f"- Vocabulary size: {index_manifest.get('vocabulary_size', 0)}")
    lines.append(f"- Index path: `{index_manifest.get('index_path', '')}`")
    lines.append(f"- Source chunk manifest: `{index_manifest.get('source_chunk_manifest_path', '')}`")
    lines.append(f"- Index failures: {len(index_manifest.get('failures', []))}")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "Gate 3 builds deterministic lexical retrieval over Gate 2 PFDS chunks. "
        "The index is a retrieval substrate only; it does not generate upgrade impact analysis or infer business truth. "
        "Every returned chunk remains tied to KB, portfolio, child PDF, and bug/patch lineage."
    )
    lines.append("")

    lines.append("## Per-KB Index Breakdown")
    lines.append("")
    lines.append("| KB | Collections | Indexed Chunks | Tokens |")
    lines.append("|---|---:|---:|---:|")
    for kb_id, collection_count, chunk_count, token_count in per_kb_counts(collections):
        lines.append(f"| {markdown_escape(kb_id)} | {collection_count} | {chunk_count} | {token_count} |")
    lines.append("")

    lines.append("## Product Breakdown")
    lines.append("")
    lines.append("| Product | Collections | Indexed Chunks |")
    lines.append("|---|---:|---:|")
    for product, collection_count, chunk_count in product_counts(collections):
        lines.append(f"| {markdown_escape(product)} | {collection_count} | {chunk_count} |")
    lines.append("")

    lines.append("## Category Breakdown")
    lines.append("")
    lines.append("| Category | Collections | Indexed Chunks |")
    lines.append("|---|---:|---:|")
    for category, collection_count, chunk_count in category_counts(collections):
        lines.append(f"| {markdown_escape(category)} | {collection_count} | {chunk_count} |")
    lines.append("")

    lines.append("## Token-Heavy Collections")
    lines.append("")
    lines.append("| KB | Bug / Patch | Product | Category | Indexed Chunks | Tokens | Collection |")
    lines.append("|---|---|---|---|---:|---:|---|")
    for collection in top_token_heavy_collections(collections):
        lines.append(
            "| "
            f"{markdown_escape(collection.get('kb_document_id'))} | "
            f"{markdown_escape(collection.get('bug_patch_number'))} | "
            f"{markdown_escape(collection.get('product'))} | "
            f"{markdown_escape(collection.get('category'))} | "
            f"{collection.get('indexed_chunk_count', 0)} | "
            f"{collection.get('token_count', 0)} | "
            f"`{markdown_escape(collection.get('collection_path'))}` |"
        )
    lines.append("")

    lines.extend(render_query_section(latest_path, latest_context))

    warnings = index_manifest.get("warnings") or []
    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Write a reviewer-facing Gate 3 KB retrieval Markdown summary.")
    parser.add_argument(
        "--index-manifest",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_chunk_lexical_index_manifest.json",
        help="Path to kb_chunk_lexical_index_manifest.json.",
    )
    parser.add_argument(
        "--query-context-root",
        type=Path,
        default=root / "kbs" / "query_context",
        help="Directory containing query context artifacts.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_retrieval_summary.md",
        help="Markdown summary output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    index_manifest = read_json(args.index_manifest)
    summary = render_summary(index_manifest, args.query_context_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(summary, encoding="utf-8")

    print(f"Wrote KB retrieval summary: {args.output}")
    print(f"Indexed collections: {index_manifest.get('indexed_collection_count', 0)}")
    print(f"Indexed chunks: {index_manifest.get('indexed_chunk_count', 0)}")
    print(f"Posting rows: {index_manifest.get('posting_count', 0)}")
    print(f"Vocabulary size: {index_manifest.get('vocabulary_size', 0)}")


if __name__ == "__main__":
    main()
