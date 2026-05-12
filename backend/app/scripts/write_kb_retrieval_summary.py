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


def query_context_files(query_context_root: Path, *, limit: int = 5) -> list[tuple[Path, dict[str, Any]]]:
    if not query_context_root.exists():
        return []
    artifacts = sorted(query_context_root.glob("*.query_context.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    contexts: list[tuple[Path, dict[str, Any]]] = []
    for artifact in artifacts[:limit]:
        contexts.append((artifact, read_json(artifact)))
    return contexts


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


def render_term_diagnostics(diagnostics: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    term_diagnostics = diagnostics.get("term_diagnostics", {})
    if not term_diagnostics:
        return lines

    lines.append("### Term Diagnostics")
    lines.append("")
    lines.append("| Term | Global Postings | Filtered Postings | IDF | Candidate Limited |")
    lines.append("|---|---:|---:|---:|---|")
    for term, details in sorted(term_diagnostics.items()):
        lines.append(
            "| "
            f"{markdown_escape(term)} | "
            f"{details.get('global_posting_count', 0)} | "
            f"{details.get('filtered_posting_count', 0)} | "
            f"{details.get('idf', 0)} | "
            f"{details.get('candidate_limited', False)} |"
        )
    lines.append("")
    return lines


def render_source_diversity(diagnostics: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    source_diversity = diagnostics.get("source_diversity", {})
    if not source_diversity:
        return lines

    lines.append("### Source Diversity Controls")
    lines.append("")
    lines.append(f"- Enabled: {source_diversity.get('enabled', False)}")
    lines.append(f"- Max chunks per child PDF: {source_diversity.get('max_chunks_per_child_pdf')}")
    lines.append(f"- Max chunks per bug / patch: {source_diversity.get('max_chunks_per_bug_patch')}")
    exclusions = source_diversity.get("excluded_by_reason", {}) or {}
    if exclusions:
        lines.append("")
        lines.append("| Exclusion Reason | Count |")
        lines.append("|---|---:|")
        for reason, count in sorted(exclusions.items()):
            lines.append(f"| {markdown_escape(reason)} | {count} |")
    lines.append("")
    return lines


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
    filters = query.get("filters") or {}
    lines.append(f"- Query artifact: `{query_context_path.as_posix()}`")
    lines.append(f"- Query context schema: `{query_context.get('schema_version', 'UNKNOWN')}`")
    lines.append(f"- Query text: `{query.get('query_text', '')}`")
    lines.append(f"- Query terms: `{', '.join(query.get('query_terms', []))}`")
    lines.append(f"- Active filters: `{json.dumps(filters, sort_keys=True)}`")
    lines.append(f"- Candidate chunks: {diagnostics.get('candidate_count', 0)}")
    lines.append(f"- Scored chunks: {diagnostics.get('scored_count', 0)}")
    lines.append(f"- Post-diversity scored chunks: {diagnostics.get('post_diversity_scored_count', diagnostics.get('scored_count', 0))}")
    lines.append(f"- Returned chunks: {diagnostics.get('returned_count', 0)}")
    lines.append(f"- Ranker: `{diagnostics.get('ranker', 'UNKNOWN')}`")
    lines.append("")

    lines.extend(render_term_diagnostics(diagnostics))
    lines.extend(render_source_diversity(diagnostics))

    results = query_context.get("results", [])
    if results:
        lines.append("### Ranked Results")
        lines.append("")
        lines.append("| Rank | Score | KB | Bug / Patch | Product | Category | Matched Terms | Score Contributions |")
        lines.append("|---:|---:|---|---|---|---|---|---|")
        for result in results[:10]:
            contributions = result.get("term_score_contributions", {}) or {}
            contribution_text = ", ".join(f"{term}:{score}" for term, score in sorted(contributions.items()))
            lines.append(
                "| "
                f"{result.get('rank', '')} | "
                f"{result.get('score', '')} | "
                f"{markdown_escape(result.get('kb_document_id'))} | "
                f"{markdown_escape(result.get('bug_patch_number'))} | "
                f"{markdown_escape(result.get('product'))} | "
                f"{markdown_escape(result.get('category'))} | "
                f"{markdown_escape(', '.join(result.get('matched_terms', [])))} | "
                f"{markdown_escape(contribution_text)} |"
            )
        lines.append("")
    return lines


def render_recent_query_contexts(query_context_root: Path) -> list[str]:
    lines: list[str] = []
    contexts = query_context_files(query_context_root, limit=5)
    if not contexts:
        return lines

    lines.append("## Recent Query Context Artifacts")
    lines.append("")
    lines.append("| Artifact | Schema | Query | Filters | Returned | Diversity Enabled |")
    lines.append("|---|---|---|---|---:|---|")
    for path, context in contexts:
        query = context.get("query", {})
        diagnostics = context.get("diagnostics", {})
        source_diversity = diagnostics.get("source_diversity", {}) if isinstance(diagnostics.get("source_diversity"), dict) else {}
        lines.append(
            "| "
            f"`{markdown_escape(path.name)}` | "
            f"{markdown_escape(context.get('schema_version'))} | "
            f"{markdown_escape(query.get('query_text'))} | "
            f"`{markdown_escape(json.dumps(query.get('filters') or {}, sort_keys=True))}` | "
            f"{diagnostics.get('returned_count', 0)} | "
            f"{source_diversity.get('enabled', False)} |"
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
        "Gate 4 extends deterministic lexical retrieval with explainability and controls. "
        "The retrieval layer can now show why each term contributed, constrain candidates by lineage fields, "
        "and limit repeated chunks from the same source. It still does not generate upgrade impact analysis."
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
    lines.extend(render_recent_query_contexts(query_context_root))

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
    parser = argparse.ArgumentParser(description="Write a reviewer-facing KB retrieval Markdown summary.")
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
