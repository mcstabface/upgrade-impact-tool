from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.write_kb_draft_review_export import claim_lookup, evidence_lookup, render_evidence_refs


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def esc(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def badge(value: Any, *, kind: str = "neutral") -> str:
    return f'<span class="badge badge-{esc(kind)}">{esc(value)}</span>'


def render_claim_card(task: dict[str, Any], claim: dict[str, Any], evidence_by_id: dict[str, dict[str, Any]]) -> str:
    evidence_ids = task.get("evidence_ids") or []
    evidence_refs = render_evidence_refs(evidence_ids, evidence_by_id)
    caveats = claim.get("caveats") or []
    caveat_html = "".join(f"<li>{esc(caveat)}</li>" for caveat in caveats)
    evidence_rows: list[str] = []
    for evidence_id in evidence_ids:
        item = evidence_by_id.get(evidence_id) or {}
        flags = item.get("pdf_context_flags") or {}
        evidence_rows.append(
            "<tr>"
            f"<td><code>{esc(evidence_id)}</code></td>"
            f"<td>{esc(item.get('kb_document_id'))}</td>"
            f"<td>{esc(item.get('bug_patch_number'))}</td>"
            f"<td>{esc(item.get('product'))}</td>"
            f"<td>{esc(item.get('category'))}</td>"
            f"<td>{esc(flags.get('has_images'))}</td>"
            f"<td>{esc(flags.get('image_count'))}</td>"
            f"<td>{esc(item.get('child_pdf_path'))}</td>"
            "</tr>"
        )
    evidence_table = ""
    if evidence_rows:
        evidence_table = (
            "<details><summary>Evidence lineage</summary>"
            "<table><thead><tr><th>Evidence ID</th><th>KB</th><th>Bug / Patch</th><th>Product</th><th>Category</th><th>Has Images</th><th>Image Count</th><th>Child PDF</th></tr></thead>"
            f"<tbody>{''.join(evidence_rows)}</tbody></table></details>"
        )
    return f"""
    <article class="claim-card" id="{esc(task.get('claim_id'))}">
      <header>
        <h3><code>{esc(task.get('claim_id'))}</code></h3>
        <div class="badges">
          {badge(task.get('claim_type'))}
          {badge(task.get('review_status'), kind='warning')}
          {badge('decision: ' + str(task.get('reviewer_decision')), kind='warning')}
          {badge('evidence review' if task.get('requires_evidence_review') else 'no evidence review')}
          {badge('visual review required' if task.get('requires_visual_review') else 'no visual review', kind='danger' if task.get('requires_visual_review') else 'neutral')}
        </div>
      </header>
      <p class="section-label">{esc(claim.get('section_title') or task.get('section_id'))}</p>
      <p>{esc(claim.get('text'))}</p>
      {('<ul class="caveats">' + caveat_html + '</ul>') if caveat_html else ''}
      <p class="evidence-ref">{esc(evidence_refs)}</p>
      {evidence_table}
      <footer>
        <label>Reviewer decision <input readonly value="{esc(task.get('reviewer_decision'))}" /></label>
        <label>Reviewer notes <textarea readonly>{esc(task.get('reviewer_notes'))}</textarea></label>
      </footer>
    </article>
    """


def render_gap_card(task: dict[str, Any]) -> str:
    return f"""
    <article class="gap-card" id="{esc(task.get('gap_id'))}">
      <header>
        <h3><code>{esc(task.get('gap_id'))}</code></h3>
        <div class="badges">
          {badge(task.get('review_status'), kind='warning')}
          {badge('ack: ' + str(task.get('acknowledgement_status')), kind='warning')}
        </div>
      </header>
      <p>{esc(task.get('gap_text'))}</p>
      <footer>
        <label>Acknowledgement <input readonly value="{esc(task.get('acknowledgement_status'))}" /></label>
        <label>Reviewer notes <textarea readonly>{esc(task.get('reviewer_notes'))}</textarea></label>
      </footer>
    </article>
    """


def render_static_ui(manifest: dict[str, Any], draft: dict[str, Any], context: dict[str, Any]) -> str:
    diagnostics = manifest.get("diagnostics", {})
    policy = manifest.get("review_policy", {})
    claims = claim_lookup(draft)
    evidence_by_id = evidence_lookup(context)
    claim_cards = "\n".join(
        render_claim_card(task, claims.get(task.get("claim_id"), {}), evidence_by_id)
        for task in manifest.get("claim_review_tasks", [])
    )
    gap_cards = "\n".join(render_gap_card(task) for task in manifest.get("unresolved_gap_tasks", []))
    policy_items = "".join(f"<li><strong>{esc(key)}</strong>: <code>{esc(value)}</code></li>" for key, value in sorted(policy.items()))
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>KB Draft Review Surface</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #0f172a; color: #e5e7eb; }}
    body {{ margin: 0; padding: 2rem; }}
    main {{ max-width: 1280px; margin: 0 auto; }}
    h1, h2, h3 {{ color: #f8fafc; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin: 1rem 0 2rem; }}
    .metric, .claim-card, .gap-card, .policy {{ background: #111827; border: 1px solid #334155; border-radius: 0.75rem; padding: 1rem; box-shadow: 0 10px 30px rgba(0,0,0,0.25); }}
    .metric span {{ display: block; color: #94a3b8; font-size: 0.85rem; }}
    .metric strong {{ display: block; font-size: 1.5rem; margin-top: 0.25rem; }}
    .claim-card, .gap-card {{ margin: 1rem 0; }}
    .badges {{ display: flex; gap: 0.5rem; flex-wrap: wrap; margin: 0.5rem 0; }}
    .badge {{ border-radius: 999px; padding: 0.2rem 0.6rem; font-size: 0.8rem; background: #1e293b; color: #cbd5e1; border: 1px solid #475569; }}
    .badge-warning {{ background: #422006; border-color: #92400e; color: #fde68a; }}
    .badge-danger {{ background: #450a0a; border-color: #991b1b; color: #fecaca; }}
    .section-label, .evidence-ref {{ color: #94a3b8; }}
    code {{ color: #93c5fd; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 1rem; font-size: 0.85rem; }}
    th, td {{ border: 1px solid #334155; padding: 0.45rem; text-align: left; vertical-align: top; }}
    th {{ background: #1e293b; }}
    input, textarea {{ width: 100%; box-sizing: border-box; margin-top: 0.25rem; background: #020617; color: #e5e7eb; border: 1px solid #475569; border-radius: 0.4rem; padding: 0.45rem; }}
    footer {{ display: grid; grid-template-columns: 1fr 2fr; gap: 1rem; margin-top: 1rem; }}
    .notice {{ border-left: 4px solid #60a5fa; padding: 1rem; background: #0b1220; color: #bfdbfe; }}
  </style>
</head>
<body>
<main>
  <h1>KB Draft Review Surface</h1>
  <p class="notice">Read-only Gate 11 surface. Review mutation must use Gate 10 update commands and validation; this page does not write state.</p>
  <section class="summary-grid">
    <div class="metric"><span>Review status</span><strong>{esc(manifest.get('review_status'))}</strong></div>
    <div class="metric"><span>Claim tasks</span><strong>{esc(diagnostics.get('claim_review_tasks'))}</strong></div>
    <div class="metric"><span>Evidence review tasks</span><strong>{esc(diagnostics.get('evidence_review_tasks'))}</strong></div>
    <div class="metric"><span>Visual review tasks</span><strong>{esc(diagnostics.get('visual_review_tasks'))}</strong></div>
    <div class="metric"><span>Unresolved gap tasks</span><strong>{esc(diagnostics.get('unresolved_gap_tasks'))}</strong></div>
    <div class="metric"><span>Finalization allowed</span><strong>{esc(policy.get('finalization_allowed'))}</strong></div>
  </section>
  <section class="policy">
    <h2>Review Policy</h2>
    <ul>{policy_items}</ul>
  </section>
  <section>
    <h2>Claim Review Tasks</h2>
    {claim_cards}
  </section>
  <section>
    <h2>Unresolved Gap Acknowledgement Tasks</h2>
    {gap_cards}
  </section>
</main>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Write a read-only static Gate 11 KB draft review UI surface.")
    parser.add_argument("--manifest", type=Path, default=root / "kbs" / "review" / "kb_draft_review_manifest.v1.json")
    parser.add_argument("--draft", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_draft.v1.json")
    parser.add_argument("--context", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_context.v2.enriched.json")
    parser.add_argument("--output", type=Path, default=root / "kbs" / "manifests" / "kb_draft_review_surface.html")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = read_json(args.manifest)
    draft = read_json(args.draft)
    context = read_json(args.context)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_static_ui(manifest, draft, context), encoding="utf-8")
    diagnostics = manifest.get("diagnostics", {})
    print(f"Wrote KB draft review static UI: {args.output}")
    print(f"Claim review tasks: {diagnostics.get('claim_review_tasks', 0)}")
    print(f"Visual review tasks: {diagnostics.get('visual_review_tasks', 0)}")
    print(f"Unresolved gap tasks: {diagnostics.get('unresolved_gap_tasks', 0)}")


if __name__ == "__main__":
    main()
