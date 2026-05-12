from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def markdown_escape(value: Any) -> str:
    text = "UNKNOWN" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def render_summary(context: dict[str, Any], skeleton: dict[str, Any]) -> str:
    diagnostics = context.get("diagnostics", {})
    exception_context = context.get("evidence_exception_context", {})
    sections = skeleton.get("sections", [])
    lines: list[str] = []
    lines.append("# KB Impact Draft Skeleton Summary")
    lines.append("")
    lines.append(f"Generated UTC: `{skeleton.get('generated_utc', '')}`")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Enriched context schema: `{context.get('schema_version', '')}`")
    lines.append(f"- Enriched context status: `{context.get('assembly_status', '')}`")
    lines.append(f"- Skeleton schema: `{skeleton.get('schema_version', '')}`")
    lines.append(f"- Skeleton status: `{skeleton.get('skeleton_status', '')}`")
    lines.append(f"- Evidence items: {diagnostics.get('assembled_evidence_items', 0)}")
    lines.append(f"- Evidence groups: {diagnostics.get('evidence_groups', 0)}")
    lines.append(f"- Image-bearing evidence items: {diagnostics.get('image_bearing_evidence_items', 0)}")
    lines.append(f"- High-severity evidence exceptions: {diagnostics.get('high_severity_evidence_exceptions', 0)}")
    lines.append(f"- Skeleton sections: {skeleton.get('diagnostics', {}).get('section_count', len(sections))}")
    lines.append("")
    lines.append("## Generation Policy")
    lines.append("")
    for key, value in sorted((skeleton.get("generation_policy") or {}).items()):
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append(
        "Gate 7 enriches the evidence packet and creates a draft container. "
        "The skeleton contains sections, evidence references, and unresolved gap placeholders only. "
        "It does not contain generated impact conclusions."
    )
    lines.append("")

    lines.append("## Skeleton Sections")
    lines.append("")
    lines.append("| Section | Status | Evidence IDs | Content Present |")
    lines.append("|---|---|---:|---|")
    for section in sections:
        lines.append(
            "| "
            f"{markdown_escape(section.get('title'))} | "
            f"{markdown_escape(section.get('status'))} | "
            f"{len(section.get('evidence_ids') or [])} | "
            f"{bool(section.get('content'))} |"
        )
    lines.append("")

    lines.append("## Evidence Exception Context")
    lines.append("")
    lines.append("### Status Counts")
    lines.append("")
    lines.append("| Status | Count |")
    lines.append("|---|---:|")
    for status, count in sorted((exception_context.get("status_counts") or {}).items()):
        lines.append(f"| {markdown_escape(status)} | {count} |")
    lines.append("")
    lines.append("### High-Severity Exceptions")
    lines.append("")
    lines.append("| KB | MP | Bug / Patch | Product | Category | Description |")
    lines.append("|---|---|---|---|---|---|")
    for exception in exception_context.get("high_severity_exceptions", []):
        lines.append(
            "| "
            f"{markdown_escape(exception.get('kb_document_id'))} | "
            f"{markdown_escape(exception.get('maintenance_pack'))} | "
            f"{markdown_escape(exception.get('bug_patch_number'))} | "
            f"{markdown_escape(exception.get('product'))} | "
            f"{markdown_escape(exception.get('category'))} | "
            f"{markdown_escape(exception.get('description'))} |"
        )
    lines.append("")

    lines.append("## PDF Context Flags")
    lines.append("")
    lines.append("| Evidence ID | Bug / Patch | Product | Category | Has Images | Image Count | Highlights | Text Status |")
    lines.append("|---|---|---|---|---|---:|---|---|")
    for item in context.get("evidence_items", []):
        flags = item.get("pdf_context_flags") or {}
        lines.append(
            "| "
            f"{markdown_escape(item.get('evidence_id'))} | "
            f"{markdown_escape(item.get('bug_patch_number'))} | "
            f"{markdown_escape(item.get('product'))} | "
            f"{markdown_escape(item.get('category'))} | "
            f"{flags.get('has_images')} | "
            f"{flags.get('image_count')} | "
            f"{flags.get('has_highlight_annotations')} | "
            f"{markdown_escape(flags.get('text_extraction_status'))} |"
        )
    lines.append("")
    lines.append("## Source Inputs")
    lines.append("")
    for key, value in sorted((context.get("source_inputs") or {}).items()):
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Write a reviewer-facing Gate 7 impact draft skeleton summary.")
    parser.add_argument("--context", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_context.v2.enriched.json")
    parser.add_argument("--skeleton", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_draft_skeleton.v1.json")
    parser.add_argument("--output", type=Path, default=root / "kbs" / "manifests" / "kb_impact_draft_skeleton_summary.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    context = read_json(args.context)
    skeleton = read_json(args.skeleton)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_summary(context, skeleton), encoding="utf-8")
    print(f"Wrote KB impact draft skeleton summary: {args.output}")
    print(f"Sections: {len(skeleton.get('sections', []))}")
    print(f"Evidence items: {len(context.get('evidence_items', []))}")


if __name__ == "__main__":
    main()
