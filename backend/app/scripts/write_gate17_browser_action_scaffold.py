from __future__ import annotations

import argparse
import html
import json
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


CLAIM_VALUES = ["ACCEPT", "REJECT", "NEEDS_MORE_EVIDENCE", "UNSET"]
GAP_VALUES = ["ACKNOWLEDGED", "NEEDS_MORE_EVIDENCE", "UNSET"]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return payload


def esc(value: Any) -> str:
    if value is None:
        return ""
    return html.escape(str(value), quote=True)


def option(value: str, label: str | None = None) -> str:
    return f'<option value="{esc(value)}">{esc(label or value)}</option>'


def render_claim_option(task: dict[str, Any]) -> str:
    claim_id = str(task.get("claim_id") or "")
    claim_type = str(task.get("claim_type") or "UNKNOWN")
    review_status = str(task.get("review_status") or "UNKNOWN")
    visual = "visual" if task.get("requires_visual_review") else "no-visual"
    return option(claim_id, f"{claim_id} · {claim_type} · {review_status} · {visual}")


def render_gap_option(task: dict[str, Any]) -> str:
    gap_id = str(task.get("gap_id") or "")
    review_status = str(task.get("review_status") or "UNKNOWN")
    ack = str(task.get("acknowledgement_status") or "UNKNOWN")
    return option(gap_id, f"{gap_id} · {review_status} · ack={ack}")


def render_scaffold(manifest: dict[str, Any], *, default_endpoint_url: str) -> str:
    diagnostics = manifest.get("diagnostics") or {}
    policy = manifest.get("review_policy") or {}
    claim_tasks = manifest.get("claim_review_tasks") or []
    gap_tasks = manifest.get("unresolved_gap_tasks") or []
    claim_options = "\n".join(render_claim_option(task) for task in claim_tasks)
    gap_options = "\n".join(render_gap_option(task) for task in gap_tasks)
    claim_value_options = "\n".join(option(value) for value in CLAIM_VALUES)
    gap_value_options = "\n".join(option(value) for value in GAP_VALUES)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>Gate 17 Browser Action Scaffold</title>
  <style>
    :root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; background: #0f172a; color: #e5e7eb; }}
    body {{ margin: 0; padding: 2rem; }}
    main {{ max-width: 1120px; margin: 0 auto; }}
    h1, h2, h3 {{ color: #f8fafc; }}
    .notice {{ border-left: 4px solid #60a5fa; padding: 1rem; background: #0b1220; color: #bfdbfe; margin: 1rem 0; }}
    .danger {{ border-left-color: #f87171; color: #fecaca; }}
    .summary-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 1rem; margin: 1rem 0 2rem; }}
    .metric, .panel {{ background: #111827; border: 1px solid #334155; border-radius: 0.75rem; padding: 1rem; box-shadow: 0 10px 30px rgba(0,0,0,0.25); }}
    .metric span {{ display: block; color: #94a3b8; font-size: 0.85rem; }}
    .metric strong {{ display: block; font-size: 1.5rem; margin-top: 0.25rem; }}
    label {{ display: block; margin: 0.9rem 0; color: #cbd5e1; }}
    input, textarea, select, button {{ width: 100%; box-sizing: border-box; margin-top: 0.25rem; background: #020617; color: #e5e7eb; border: 1px solid #475569; border-radius: 0.4rem; padding: 0.55rem; }}
    textarea {{ min-height: 6rem; }}
    button {{ cursor: pointer; background: #1d4ed8; border-color: #2563eb; font-weight: 700; }}
    button:disabled {{ cursor: not-allowed; background: #1e293b; color: #64748b; border-color: #334155; }}
    code, pre {{ color: #93c5fd; }}
    pre {{ background: #020617; border: 1px solid #334155; border-radius: 0.75rem; padding: 1rem; overflow: auto; }}
    .row {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }}
    .checkbox-line {{ display: flex; align-items: center; gap: 0.6rem; }}
    .checkbox-line input {{ width: auto; }}
    .hidden {{ display: none; }}
  </style>
</head>
<body>
<main>
  <h1>Gate 17 Browser Action Scaffold</h1>
  <p class="notice">This page is a local browser scaffold. It does not directly edit JSON. It sends a Gate 13 review update request to the guarded <code>POST /review/update</code> endpoint.</p>
  <p class="notice danger">Finalization remains disabled. This scaffold is not production auth. Authorization, provenance, mutation audit, security-denial audit, and artifact regeneration still happen server-side.</p>

  <section class="summary-grid">
    <div class="metric"><span>Review status</span><strong>{esc(manifest.get('review_status'))}</strong></div>
    <div class="metric"><span>Claim tasks</span><strong>{esc(diagnostics.get('claim_review_tasks'))}</strong></div>
    <div class="metric"><span>Visual review tasks</span><strong>{esc(diagnostics.get('visual_review_tasks'))}</strong></div>
    <div class="metric"><span>Unresolved gaps</span><strong>{esc(diagnostics.get('unresolved_gap_tasks'))}</strong></div>
    <div class="metric"><span>Finalization allowed</span><strong>{esc(policy.get('finalization_allowed'))}</strong></div>
  </section>

  <section class="panel">
    <h2>Guarded update request</h2>
    <form id="review-action-form">
      <div class="row">
        <label>Endpoint URL
          <input id="endpoint-url" value="{esc(default_endpoint_url)}" />
        </label>
        <label>Reviewer ID
          <input id="reviewer" placeholder="GATE15_AUTH_SMOKE" />
        </label>
      </div>
      <div class="row">
        <label>Request ID
          <input id="request-id" placeholder="gate17-browser-0001" />
        </label>
        <label>Action
          <select id="action">
            <option value="claim">claim</option>
            <option value="gap">gap</option>
          </select>
        </label>
      </div>
      <label id="claim-target-label">Claim target
        <select id="claim-target">{claim_options}</select>
      </label>
      <label id="gap-target-label" class="hidden">Gap target
        <select id="gap-target">{gap_options}</select>
      </label>
      <label id="claim-value-label">Claim decision
        <select id="claim-value">{claim_value_options}</select>
      </label>
      <label id="gap-value-label" class="hidden">Gap acknowledgement
        <select id="gap-value">{gap_value_options}</select>
      </label>
      <label>Reviewer notes
        <textarea id="notes" placeholder="Bounded reviewer note for the audit trail."></textarea>
      </label>
      <label class="checkbox-line">
        <input id="visual-acknowledged" type="checkbox" />
        <span>Visual evidence acknowledged where required</span>
      </label>
      <label class="checkbox-line">
        <input id="enable-post" type="checkbox" />
        <span>I understand this will call the guarded endpoint. No direct JSON mutation is performed by this page.</span>
      </label>
      <button id="submit-button" type="submit" disabled>POST guarded review update</button>
    </form>
  </section>

  <section class="panel">
    <h2>Request preview</h2>
    <pre id="request-preview"></pre>
  </section>

  <section class="panel">
    <h2>Endpoint response</h2>
    <pre id="response-output">No request sent.</pre>
  </section>
</main>
<script>
const actionEl = document.getElementById('action');
const enableEl = document.getElementById('enable-post');
const submitEl = document.getElementById('submit-button');
const responseEl = document.getElementById('response-output');
const previewEl = document.getElementById('request-preview');

function activePayload() {{
  const action = actionEl.value;
  const payload = {{
    action,
    target_id: action === 'claim' ? document.getElementById('claim-target').value : document.getElementById('gap-target').value,
    value: action === 'claim' ? document.getElementById('claim-value').value : document.getElementById('gap-value').value,
    reviewer: document.getElementById('reviewer').value.trim(),
    notes: document.getElementById('notes').value,
    visual_acknowledged: document.getElementById('visual-acknowledged').checked
  }};
  return payload;
}}

function updateVisibility() {{
  const isClaim = actionEl.value === 'claim';
  document.getElementById('claim-target-label').classList.toggle('hidden', !isClaim);
  document.getElementById('claim-value-label').classList.toggle('hidden', !isClaim);
  document.getElementById('gap-target-label').classList.toggle('hidden', isClaim);
  document.getElementById('gap-value-label').classList.toggle('hidden', isClaim);
  submitEl.disabled = !enableEl.checked;
  previewEl.textContent = JSON.stringify(activePayload(), null, 2);
}}

document.getElementById('review-action-form').addEventListener('input', updateVisibility);
document.getElementById('review-action-form').addEventListener('change', updateVisibility);

document.getElementById('review-action-form').addEventListener('submit', async (event) => {{
  event.preventDefault();
  if (!enableEl.checked) {{ return; }}
  const endpointUrl = document.getElementById('endpoint-url').value.trim();
  const requestId = document.getElementById('request-id').value.trim();
  const payload = activePayload();
  responseEl.textContent = 'Submitting guarded endpoint request...';
  try {{
    const response = await fetch(endpointUrl, {{
      method: 'POST',
      headers: {{
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'X-Request-Id': requestId,
        'X-Review-Source': 'gate17-browser-action-scaffold'
      }},
      body: JSON.stringify(payload)
    }});
    const text = await response.text();
    let rendered = text;
    try {{ rendered = JSON.stringify(JSON.parse(text), null, 2); }} catch (_err) {{}}
    responseEl.textContent = `HTTP ${{response.status}}\n${{rendered}}`;
  }} catch (err) {{
    responseEl.textContent = `REQUEST FAILED\n${{err}}`;
  }}
}});

updateVisibility();
</script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Write a local Gate 17 browser action scaffold for guarded review updates.")
    parser.add_argument("--manifest", type=Path, default=root / "kbs" / "review" / "kb_draft_review_manifest.v1.json")
    parser.add_argument("--output", type=Path, default=root / "kbs" / "manifests" / "kb_draft_review_action_scaffold.gate17.html")
    parser.add_argument("--endpoint-url", default="http://127.0.0.1:8766/review/update")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = read_json(args.manifest)
    html_text = render_scaffold(manifest, default_endpoint_url=args.endpoint_url)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html_text, encoding="utf-8")
    diagnostics = manifest.get("diagnostics") or {}
    print(f"[gate17:write] Wrote browser action scaffold: {args.output}")
    print(f"[gate17:write] claim_review_tasks={diagnostics.get('claim_review_tasks', 0)}")
    print(f"[gate17:write] unresolved_gap_tasks={diagnostics.get('unresolved_gap_tasks', 0)}")
    print("[gate17:write] mutation_path=POST /review/update only")


if __name__ == "__main__":
    main()
