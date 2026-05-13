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


def claim_lookup(draft: dict[str, Any]) -> dict[str, dict[str, Any]]:
    claims: dict[str, dict[str, Any]] = {}
    for section in draft.get("sections", []):
        for claim in section.get("claims", []) or []:
            claims[claim.get("claim_id")] = {
                "section_title": section.get("title"),
                "section_id": section.get("section_id"),
                **claim,
            }
    return claims


def evidence_lookup(context: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {item["evidence_id"]: item for item in context.get("evidence_items", []) if item.get("evidence_id")}


def render_evidence_refs(evidence_ids: list[str], evidence_by_id: dict[str, dict[str, Any]]) -> str:
    refs: list[str] = []
    for evidence_id in evidence_ids:
        item = evidence_by_id.get(evidence_id) or {}
        refs.append(
            f"{evidence_id} ({item.get('kb_document_id')} / bug {item.get('bug_patch_number')} / {item.get('product')} / {item.get('category')})"
        )
    return "; ".join(refs)


def render_export(manifest: dict[str, Any], draft: dict[str, Any], context: dict[str, Any]) -> str:
    diagnostics = manifest.get("diagnostics", {})
    policy = manifest.get("review_policy", {})
    claims = claim_lookup(draft)
    evidence_by_id = evidence_lookup(context)

    lines: list[str] = []
    lines.append("# KB Draft Review Export")
    lines.append("")
    lines.append(f"Generated UTC: `{manifest.get('generated_utc', '')}`")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Artifact type: `{manifest.get('artifact_type', '')}`")
    lines.append(f"- Schema version: `{manifest.get('schema_version', '')}`")
    lines.append(f"- Review status: `{manifest.get('review_status', '')}`")
    lines.append(f"- Claim review tasks: {diagnostics.get('claim_review_tasks', 0)}")
    lines.append(f"- Evidence review tasks: {diagnostics.get('evidence_review_tasks', 0)}")
    lines.append(f"- Visual review tasks: {diagnostics.get('visual_review_tasks', 0)}")
    lines.append(f"- Unresolved gap tasks: {diagnostics.get('unresolved_gap_tasks', 0)}")
    lines.append(f"- Finalization allowed: `{policy.get('finalization_allowed')}`")
    lines.append("")
    lines.append("## Review Policy")
    lines.append("")
    for key, value in sorted(policy.items()):
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    lines.append("## Claim Review Tasks")
    lines.append("")
    lines.append("| Claim | Section | Type | Status | Decision | Evidence Review | Visual Review | Evidence |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for task in manifest.get("claim_review_tasks", []):
        claim = claims.get(task.get("claim_id"), {})
        lines.append(
            "| "
            f"`{markdown_escape(task.get('claim_id'))}` | "
            f"{markdown_escape(claim.get('section_title') or task.get('section_id'))} | "
            f"{markdown_escape(task.get('claim_type'))} | "
            f"{markdown_escape(task.get('review_status'))} | "
            f"{markdown_escape(task.get('reviewer_decision'))} | "
            f"{task.get('requires_evidence_review')} | "
            f"{task.get('requires_visual_review')} | "
            f"{markdown_escape(render_evidence_refs(task.get('evidence_ids') or [], evidence_by_id))} |"
        )
    lines.append("")
    lines.append("## Claim Text for Review")
    lines.append("")
    for task in manifest.get("claim_review_tasks", []):
        claim = claims.get(task.get("claim_id"), {})
        lines.append(f"### `{task.get('claim_id')}` — {claim.get('section_title', task.get('section_id'))}")
        lines.append("")
        lines.append(claim.get("text", ""))
        lines.append("")
        if claim.get("caveats"):
            for caveat in claim.get("caveats"):
                lines.append(f"- Caveat: {caveat}")
            lines.append("")
        lines.append("Reviewer decision: `UNSET`  ")
        lines.append("Reviewer notes:  ")
        lines.append("")

    lines.append("## Unresolved Gap Acknowledgement Tasks")
    lines.append("")
    lines.append("| Gap | Status | Acknowledgement | Gap Text |")
    lines.append("|---|---|---|---|")
    for task in manifest.get("unresolved_gap_tasks", []):
        lines.append(
            "| "
            f"`{markdown_escape(task.get('gap_id'))}` | "
            f"{markdown_escape(task.get('review_status'))} | "
            f"{markdown_escape(task.get('acknowledgement_status'))} | "
            f"{markdown_escape(task.get('gap_text'))} |"
        )
    lines.append("")
    lines.append("## Source Inputs")
    lines.append("")
    lines.append(f"- Source draft: `{manifest.get('source_draft_path', '')}`")
    lines.append(f"- Source context: `{manifest.get('source_context_path', '')}`")
    lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Write reviewer-facing Gate 9 draft review export.")
    parser.add_argument("--manifest", type=Path, default=root / "kbs" / "review" / "kb_draft_review_manifest.v1.json")
    parser.add_argument("--draft", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_draft.v1.json")
    parser.add_argument("--context", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_context.v2.enriched.json")
    parser.add_argument("--output", type=Path, default=root / "kbs" / "manifests" / "kb_draft_review_export.md")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = read_json(args.manifest)
    draft = read_json(args.draft)
    context = read_json(args.context)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_export(manifest, draft, context), encoding="utf-8")
    diagnostics = manifest.get("diagnostics", {})
    print(f"Wrote KB draft review export: {args.output}")
    print(f"Claim review tasks: {diagnostics.get('claim_review_tasks', 0)}")
    print(f"Visual review tasks: {diagnostics.get('visual_review_tasks', 0)}")
    print(f"Unresolved gap tasks: {diagnostics.get('unresolved_gap_tasks', 0)}")


if __name__ == "__main__":
    main()
