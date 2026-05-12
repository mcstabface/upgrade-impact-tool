from __future__ import annotations

import argparse
import json
from collections import Counter
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


def product_breakdown(items: list[dict[str, Any]]) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for item in items:
        counts[value_or_unknown(item.get("product"))] += 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def category_breakdown(items: list[dict[str, Any]]) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for item in items:
        counts[value_or_unknown(item.get("category"))] += 1
    return sorted(counts.items(), key=lambda item: (-item[1], item[0]))


def case_breakdown(items: list[dict[str, Any]]) -> list[tuple[str, int]]:
    counts: Counter[str] = Counter()
    for item in items:
        counts[value_or_unknown(item.get("case_id"))] += 1
    return sorted(counts.items(), key=lambda item: item[0])


def render_summary(context: dict[str, Any]) -> str:
    diagnostics = context.get("diagnostics", {})
    policy = context.get("generation_policy", {})
    groups = context.get("evidence_groups", [])
    items = context.get("evidence_items", [])

    lines: list[str] = []
    lines.append("# KB Impact Context Summary")
    lines.append("")
    lines.append(f"Generated UTC: `{context.get('generated_utc', '')}`")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Artifact type: `{context.get('artifact_type', '')}`")
    lines.append(f"- Schema version: `{context.get('schema_version', '')}`")
    lines.append(f"- Assembly status: `{context.get('assembly_status', '')}`")
    lines.append(f"- Evidence items: {diagnostics.get('assembled_evidence_items', 0)}")
    lines.append(f"- Evidence groups: {diagnostics.get('evidence_groups', 0)}")
    lines.append(f"- Unique bug / patch numbers: {diagnostics.get('unique_bug_patch_numbers', 0)}")
    lines.append(f"- Unique child PDFs: {diagnostics.get('unique_child_pdfs', 0)}")
    lines.append(f"- Warnings: {len(context.get('warnings', []))}")
    lines.append("")
    lines.append("## Generation Policy")
    lines.append("")
    lines.append(f"- LLM used: {policy.get('llm_used')}")
    lines.append(f"- Impact claims generated: {policy.get('impact_claims_generated')}")
    lines.append(f"- Summaries generated: {policy.get('summaries_generated')}")
    lines.append(f"- Allowed use: {policy.get('allowed_use', '')}")
    lines.append(f"- Prohibited use: {policy.get('prohibited_use', '')}")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "This artifact is an evidence packet only. It assembles retrieved PFDS chunks, scores, and KB/PFDS lineage "
        "for reviewer inspection and later constrained impact-draft generation. It contains no generated impact analysis."
    )
    lines.append("")

    lines.append("## Evidence by Evaluation Case")
    lines.append("")
    lines.append("| Case | Evidence Items |")
    lines.append("|---|---:|")
    for case_id, count in case_breakdown(items):
        lines.append(f"| {markdown_escape(case_id)} | {count} |")
    lines.append("")

    lines.append("## Product Breakdown")
    lines.append("")
    lines.append("| Product | Evidence Items |")
    lines.append("|---|---:|")
    for product, count in product_breakdown(items):
        lines.append(f"| {markdown_escape(product)} | {count} |")
    lines.append("")

    lines.append("## Category Breakdown")
    lines.append("")
    lines.append("| Category | Evidence Items |")
    lines.append("|---|---:|")
    for category, count in category_breakdown(items):
        lines.append(f"| {markdown_escape(category)} | {count} |")
    lines.append("")

    lines.append("## Evidence Groups")
    lines.append("")
    lines.append("| Group | KB | Bug / Patch | Product | Category | Evidence Count | Max Score | Child PDFs |")
    lines.append("|---|---|---|---|---|---:|---:|---:|")
    for group in groups:
        lines.append(
            "| "
            f"{markdown_escape(group.get('group_key'))} | "
            f"{markdown_escape(group.get('kb_document_id'))} | "
            f"{markdown_escape(group.get('bug_patch_number'))} | "
            f"{markdown_escape(group.get('product'))} | "
            f"{markdown_escape(group.get('category'))} | "
            f"{group.get('evidence_count', 0)} | "
            f"{group.get('max_score', 0)} | "
            f"{len(group.get('child_pdf_paths') or [])} |"
        )
    lines.append("")

    lines.append("## Top Evidence Items")
    lines.append("")
    lines.append("| Case | Rank | Score | KB | Bug / Patch | Product | Category | Chunk |")
    lines.append("|---|---:|---:|---|---|---|---|---|")
    for item in sorted(items, key=lambda i: (value_or_unknown(i.get("case_id")), int(i.get("rank") or 0)))[:25]:
        lines.append(
            "| "
            f"{markdown_escape(item.get('case_id'))} | "
            f"{item.get('rank', 0)} | "
            f"{item.get('score', 0)} | "
            f"{markdown_escape(item.get('kb_document_id'))} | "
            f"{markdown_escape(item.get('bug_patch_number'))} | "
            f"{markdown_escape(item.get('product'))} | "
            f"{markdown_escape(item.get('category'))} | "
            f"`{markdown_escape(item.get('chunk_id'))}` |"
        )
    lines.append("")

    warnings = context.get("warnings") or []
    if warnings:
        lines.append("## Warnings")
        lines.append("")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    lines.append("## Source Inputs")
    lines.append("")
    for key, value in sorted((context.get("source_inputs") or {}).items()):
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Write a reviewer-facing Gate 6 impact context summary.")
    parser.add_argument(
        "--context",
        type=Path,
        default=root / "kbs" / "impact_context" / "kb_impact_context.v1.json",
        help="Impact context artifact path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_impact_context_summary.md",
        help="Markdown summary output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    context = read_json(args.context)
    summary = render_summary(context)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(summary, encoding="utf-8")

    diagnostics = context.get("diagnostics", {})
    print(f"Wrote KB impact context summary: {args.output}")
    print(f"Evidence items: {diagnostics.get('assembled_evidence_items', 0)}")
    print(f"Evidence groups: {diagnostics.get('evidence_groups', 0)}")


if __name__ == "__main__":
    main()
