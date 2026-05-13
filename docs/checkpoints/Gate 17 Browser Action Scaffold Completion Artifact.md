# Gate 17 Browser Action Scaffold Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: Browser Action Scaffold Against Guarded Endpoint  
Status: Complete for current local scaffold slice  
Generated: 2026-05-13

## Purpose

This checkpoint captures the completed state of Gate 17 for the KB review workflow.

Gate 17 answered this bounded question:

> Can a local browser surface prepare and submit review actions through the existing guarded endpoint without directly mutating review JSON or enabling finalization?

For the current implementation slice, the answer is yes.

Gate 17 adds a separate browser action scaffold that calls the guarded `POST /review/update` endpoint. It does not mutate review JSON directly, does not modify the Gate 11 read-only review surface, does not implement production OIDC, and does not enable finalization.

## Source Baseline

Gate 17 starts from Gate 16C guarded endpoint security-denial audit wiring.

Current Gate 16C baseline:

- guarded endpoint preflights authorization through `LocalPolicyAuthAdapter`
- endpoint health reports authorization and provenance requirements
- endpoint health reports security-denial audit enabled
- authorized reviewer mutation succeeds
- observer mutation is denied before review mutation
- missing request ID is rejected before review mutation
- endpoint denials write security-denial audit events
- security denial audit validates with `[gate16b:audit] OK`
- review mutation audit validates with `[gate12:audit] OK`
- review provenance validates with `[gate15:provenance] OK`
- mutable review state validates with `[gate10:validate] OK`
- regenerated guarded surface validates with `[gate11:validate] OK`
- finalization remains disabled

## Gate 17 Design

Gate 17 intentionally keeps the Gate 11 static review surface read-only.

The browser mutation affordance is generated as a separate local scaffold:

```text
kbs/manifests/kb_draft_review_action_scaffold.gate17.html
```

This preserves the read-only surface contract while allowing a browser to submit review actions through the existing guarded endpoint.

## Gate 17 Pipeline

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate17_browser_action_scaffold
```

Dry run:

```bash
python -m app.scripts.run_gate17_browser_action_scaffold --dry-run
```

The runner performs these steps:

1. runs `app.scripts.run_gate11_kb_review_surface`,
2. copies the base review manifest to `kbs/review/kb_draft_review_manifest.gate17_browser.json`,
3. writes the Gate 17 browser action scaffold,
4. validates the scaffold,
5. verifies expected scaffold artifacts exist.

## Generated Artifacts

| Artifact | Purpose |
|---|---|
| `kbs/review/kb_draft_review_manifest.gate17_browser.json` | Gate 17 local browser scaffold manifest copy |
| `kbs/manifests/kb_draft_review_action_scaffold.gate17.html` | Local browser action scaffold |

Manual browser smoke may additionally generate:

| Artifact | Purpose |
|---|---|
| `kbs/manifests/kb_draft_review_export.gate17_browser.md` | Guarded-regenerated review export after browser mutation |
| `kbs/manifests/kb_draft_review_surface.gate17_browser.html` | Guarded-regenerated static review surface after browser mutation |
| `kbs/audit/security_denials.gate17.jsonl` | Browser-denial security audit log |

Generated review and audit JSON/JSONL artifacts remain ignored under `kbs/review/` and `kbs/audit/`.

## Endpoint Changes

Updated script:

```text
backend/app/scripts/guarded_review_update_http_server.py
```

The guarded endpoint now supports local browser scaffold CORS/preflight for:

```text
Origin: null
Origin: http://127.0.0.1:8766
Origin: http://localhost:8766
```

This enables a static local HTML file to call the guarded endpoint during manual local smoke testing.

The endpoint health response now includes:

```text
browser_action_scaffold_allowed = true
```

Existing Gate 16C fields remain preserved:

```text
authorization_required = true
provenance_required = true
security_denial_audit_enabled = true
finalization_allowed = false
```

## Browser Scaffold Behavior

New script:

```text
backend/app/scripts/write_gate17_browser_action_scaffold.py
```

The scaffold renders:

- endpoint URL input
- reviewer ID input
- request ID input
- action selector (`claim` / `gap`)
- claim target selector
- gap target selector
- claim decision selector
- gap acknowledgement selector
- reviewer notes field
- visual acknowledgement checkbox
- explicit enable-post checkbox
- request preview panel
- endpoint response panel

The scaffold submits only to:

```text
POST /review/update
```

It sends:

```text
Content-Type: application/json
Accept: application/json
X-Request-Id: <operator provided request id>
X-Review-Source: gate17-browser-action-scaffold
```

The request body matches the Gate 13 review update request contract:

```json
{
  "action": "claim",
  "target_id": "evidence_group_006",
  "value": "ACCEPT",
  "reviewer": "GATE15_AUTH_SMOKE",
  "notes": "Bounded reviewer note.",
  "visual_acknowledged": true
}
```

For gap actions, the scaffold submits:

```json
{
  "action": "gap",
  "target_id": "gap_001",
  "value": "ACKNOWLEDGED",
  "reviewer": "GATE15_AUTH_SMOKE",
  "notes": "Bounded reviewer note.",
  "visual_acknowledged": false
}
```

The browser page does not write files, does not access local storage, and does not mutate review JSON directly.

## Scaffold Validation

New script:

```text
backend/app/scripts/validate_gate17_browser_action_scaffold.py
```

The validator requires:

- Gate 17 title text
- `POST /review/update`
- no direct JSON mutation message
- authorization/provenance/audit guardrail message
- finalization-disabled message
- `X-Request-Id`
- `X-Review-Source`
- `gate17-browser-action-scaffold`
- `visual_acknowledged`
- exactly one `fetch(` call
- POST method
- explicit enable-post gate

The validator rejects:

- direct review manifest filename references
- browser file-write APIs
- local/session storage
- finalization strings
- multiple forms
- multiple endpoint calls

## Local Validation Status

Local validation was reported complete by the operator after running the Gate 17 tests.

Expected successful command:

```bash
python -m app.scripts.run_gate17_browser_action_scaffold
```

Expected validation marker:

```text
[gate17:validate] OK
```

## Manual Browser Smoke Procedure

Start the guarded endpoint against the Gate 17 manifest:

```bash
python -m app.scripts.guarded_review_update_http_server \
  --host 127.0.0.1 \
  --port 8766 \
  --manifest ../kbs/review/kb_draft_review_manifest.gate17_browser.json \
  --export-output ../kbs/manifests/kb_draft_review_export.gate17_browser.md \
  --surface-output ../kbs/manifests/kb_draft_review_surface.gate17_browser.html \
  --security-audit-output ../kbs/audit/security_denials.gate17.jsonl
```

Open:

```text
kbs/manifests/kb_draft_review_action_scaffold.gate17.html
```

Then submit review actions only through the scaffold. Direct JSON edits remain forbidden.

## Validation Coverage

Gate 17 validates that:

- Gate 11 read-only surface still validates,
- Gate 17 scaffold can be generated from a manifest copy,
- Gate 17 scaffold contains required guarded endpoint controls,
- Gate 17 scaffold has no direct JSON mutation affordance,
- scaffold POST is explicitly gated by an operator checkbox,
- scaffold submits only one guarded endpoint call,
- finalization remains disabled.

Gate 17 reuses Gate 16C server-side validation for actual authorized mutation, denied mutation, missing provenance rejection, review mutation audit, provenance audit, security-denial audit, and regenerated surface validation.

## What This Proves

Gate 17 proves that the project can now:

- keep the static review surface read-only,
- generate a separate local browser action scaffold,
- route browser-originated review actions through the guarded endpoint,
- preserve server-side authorization/provenance/audit enforcement,
- avoid direct JSON mutation from browser code,
- preserve finalization-disabled controls.

## Known Limitations

Gate 17 remains local/prototype infrastructure.

Known limitations:

- It does not implement production OIDC.
- It does not implement reverse-proxy identity trust.
- It does not implement signed service tokens.
- It does not add a production web framework.
- It does not add session management.
- It does not provide CSRF protection.
- It does not finalize drafts.
- It does not call an LLM.

These limitations are acceptable for Gate 17. They define the next production-hardening gate.

## Recommended Next Gate

Recommended next gate:

**Gate 17A — OIDC Adapter Skeleton**

Gate 17A should add an OIDC adapter skeleton behind the existing `AuthAdapter` protocol without enabling it by default.

Proposed Gate 17A sequence:

1. Add `OIDCAuthAdapter` skeleton implementing `AuthAdapter`.
2. Add deterministic config loading for issuer, audience, and JWKS URI.
3. Validate missing/disabled OIDC config fails closed.
4. Do not replace `LocalPolicyAuthAdapter` by default.
5. Add tests/smoke runner proving OIDC skeleton is inert unless explicitly configured.
6. Keep finalization disabled.

## Completion Status

Gate 17 is complete for the current local browser scaffold slice.

The next work should begin from this checkpoint, not from memory.
