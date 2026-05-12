from __future__ import annotations

import argparse
import json
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


@dataclass(frozen=True)
class ContextRecord:
    path: Path
    context: dict[str, Any]

    @property
    def ranker(self) -> str:
        return str(self.context.get("diagnostics", {}).get("ranker") or "UNKNOWN")

    @property
    def query_text(self) -> str:
        return str(self.context.get("query", {}).get("query_text") or "")

    @property
    def filters_key(self) -> str:
        filters = self.context.get("query", {}).get("filters") or {}
        return json.dumps(filters, sort_keys=True)

    @property
    def label(self) -> str:
        return f"{self.query_text} | filters={self.filters_key}"


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


def query_context_records(query_context_root: Path, *, limit: int) -> list[ContextRecord]:
    if not query_context_root.exists():
        return []
    files = sorted(query_context_root.glob("*.query_context.json"), key=lambda path: path.stat().st_mtime, reverse=True)
    return [ContextRecord(path=path, context=read_json(path)) for path in files[:limit]]


def latest_comparable_pairs(records: list[ContextRecord]) -> list[tuple[ContextRecord, ContextRecord]]:
    grouped: defaultdict[str, dict[str, ContextRecord]] = defaultdict(dict)
    for record in records:
        if record.ranker in {"tfidf_v1", "bm25_v1"}:
            grouped[record.label].setdefault(record.ranker, record)

    pairs: list[tuple[ContextRecord, ContextRecord]] = []
    for rankers in grouped.values():
        if "tfidf_v1" in rankers and "bm25_v1" in rankers:
            pairs.append((rankers["tfidf_v1"], rankers["bm25_v1"]))
    return pairs


def result_signature(result: dict[str, Any]) -> str:
    return str(result.get("chunk_id") or "")


def render_result_table(record: ContextRecord) -> list[str]:
    lines: list[str] = []
    results = record.context.get("results", [])
    lines.append(f"### {record.ranker}: `{record.path.name}`")
    lines.append("")
    diagnostics = record.context.get("diagnostics", {})
    ranker_diagnostics = diagnostics.get("ranker_diagnostics", {})
    lines.append(f"- Returned: {diagnostics.get('returned_count', 0)}")
    lines.append(f"- Candidate chunks: {diagnostics.get('candidate_count', 0)}")
    lines.append(f"- Post-diversity scored chunks: {diagnostics.get('post_diversity_scored_count', 0)}")
    if record.ranker == "bm25_v1":
        lines.append(f"- BM25 k1: {ranker_diagnostics.get('bm25_k1')}")
        lines.append(f"- BM25 b: {ranker_diagnostics.get('bm25_b')}")
        lines.append(f"- Average document length: {ranker_diagnostics.get('average_document_length')}")
    lines.append("")
    lines.append("| Rank | Score | KB | Bug / Patch | Product | Category | Matched Terms | Contributions |")
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


def render_pair_comparison(tfidf_record: ContextRecord, bm25_record: ContextRecord) -> list[str]:
    lines: list[str] = []
    query = tfidf_record.context.get("query", {})
    filters = query.get("filters") or {}
    tfidf_results = tfidf_record.context.get("results", [])
    bm25_results = bm25_record.context.get("results", [])
    tfidf_ids = [result_signature(result) for result in tfidf_results]
    bm25_ids = [result_signature(result) for result in bm25_results]
    shared = [chunk_id for chunk_id in tfidf_ids if chunk_id in set(bm25_ids)]

    lines.append(f"## Comparison: `{markdown_escape(tfidf_record.query_text)}`")
    lines.append("")
    lines.append(f"- Filters: `{json.dumps(filters, sort_keys=True)}`")
    lines.append(f"- Shared top-result chunks: {len(shared)}")
    lines.append(f"- TF-IDF top chunk: `{tfidf_ids[0] if tfidf_ids else 'NO_RESULTS'}`")
    lines.append(f"- BM25 top chunk: `{bm25_ids[0] if bm25_ids else 'NO_RESULTS'}`")
    lines.append("")
    lines.append("| Rank | TF-IDF Chunk | BM25 Chunk | Same Chunk |")
    lines.append("|---:|---|---|---|")
    max_len = max(len(tfidf_ids), len(bm25_ids))
    for index in range(min(max_len, 10)):
        tfidf_chunk = tfidf_ids[index] if index < len(tfidf_ids) else ""
        bm25_chunk = bm25_ids[index] if index < len(bm25_ids) else ""
        lines.append(
            "| "
            f"{index + 1} | "
            f"`{markdown_escape(tfidf_chunk)}` | "
            f"`{markdown_escape(bm25_chunk)}` | "
            f"{tfidf_chunk == bm25_chunk} |"
        )
    lines.append("")
    lines.extend(render_result_table(tfidf_record))
    lines.extend(render_result_table(bm25_record))
    return lines


def render_summary(query_context_root: Path, *, limit: int) -> str:
    generated_utc = datetime.now(timezone.utc).isoformat()
    records = query_context_records(query_context_root, limit=limit)
    pairs = latest_comparable_pairs(records)

    lines: list[str] = []
    lines.append("# KB BM25 Comparison Summary")
    lines.append("")
    lines.append(f"Generated UTC: `{generated_utc}`")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Query context root: `{query_context_root.as_posix()}`")
    lines.append(f"- Query contexts inspected: {len(records)}")
    lines.append(f"- Comparable TF-IDF/BM25 pairs: {len(pairs)}")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "Gate 5 compares deterministic TF-IDF and BM25 retrieval results over the same indexed PFDS chunks. "
        "This report shows whether BM25 changes top-ranked evidence before any downstream upgrade-impact analysis consumes retrieval output."
    )
    lines.append("")

    if not pairs:
        lines.append("No comparable TF-IDF/BM25 query-context pairs were found.")
        lines.append("")
        return "\n".join(lines).rstrip() + "\n"

    for tfidf_record, bm25_record in pairs:
        lines.extend(render_pair_comparison(tfidf_record, bm25_record))

    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Write a Gate 5 TF-IDF vs BM25 retrieval comparison summary.")
    parser.add_argument(
        "--query-context-root",
        type=Path,
        default=root / "kbs" / "query_context",
        help="Directory containing query context artifacts.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_bm25_comparison_summary.md",
        help="Markdown comparison summary output path.",
    )
    parser.add_argument("--limit", type=int, default=12, help="Number of recent query contexts to inspect.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = render_summary(args.query_context_root, limit=args.limit)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(summary, encoding="utf-8")
    print(f"Wrote KB BM25 comparison summary: {args.output}")


if __name__ == "__main__":
    main()
