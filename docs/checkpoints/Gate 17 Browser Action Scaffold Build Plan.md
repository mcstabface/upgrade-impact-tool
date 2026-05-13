# Gate 17 Browser Action Scaffold Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Browser Action Scaffold Against Guarded Endpoint  
Status: Proposed / initial patches applied  
Generated: 2026-05-13

## Purpose

Gate 17 answers this bounded question:

> Can a local browser surface prepare and submit review actions through the existing guarded endpoint without directly mutating review JSON or enabling finalization?

The intended answer is yes, but only as a local scaffold. Gate 17 is not production authentication, not OIDC, not a reverse-proxy identity integration, and not a replacement for the server-side authorization/audit gates.

## Source Baseline

Gate 17 starts from Gate 16C:

- `POST /review/update` is guarded by `LocalPolicyAuthAdapter`.
- request provenance is required.
- denied requests write security-denial audit events.
- authorized mutations regenerate review export and static review surface.
- finalization remains disabled.
- Gate 11 read-only surface remains mutation-free.

## Design Decision

Gate 17 must not add mutation controls to the Gate 11 read-only surface.

Instead, Gate 17 adds a separate local browser action scaffold:

```text
kbs/manifests/kb_draft_review_action_scaffold.gate17.html
```

This preserves the Gate 11 invariant that the review surface is read-only while still proving a browser can call the guarded mutation endpoint.

## Scope

In scope:

1. Generate a static browser action scaffold from the review manifest.
2. Require reviewer ID, request ID, action, target, decision/acknowledgement, notes, and visual acknowledgement checkbox.
3. Disable POST until the operator explicitly enables endpoint submission.
4. Submit only to `POST /review/update`.
5. Send `X-Request-Id` and `X-Review-Source` headers.
6. Keep finalization disabled.
7. Validate the scaffold contains the required controls and no direct JSON mutation affordances.
8. Add local-only CORS/preflight support to the guarded endpoint so a file-opened browser scaffold can call it.

Out of scope:

- OIDC implementation.
- reverse-proxy asserted identity trust.
- signed service token support.
- production web framework.
- server-rendered session state.
- finalization.
- LLM-assisted review decisions.
- direct JSON writes from browser code.

## Initial Patches

| File | Purpose |
|---|---|
| `backend/app/scripts/guarded_review_update_http_server.py` | Adds local browser scaffold CORS/preflight support and health flag |
| `backend/app/scripts/write_gate17_browser_action_scaffold.py` | Generates the standalone Gate 17 browser scaffold HTML |
| `backend/app/scripts/validate_gate17_browser_action_scaffold.py` | Validates scaffold controls and direct-mutation guardrails |
| `backend/app/scripts/run_gate17_browser_action_scaffold.py` | Runs Gate 11 baseline, copies manifest, writes scaffold, validates scaffold |

## Acceptance Criteria

Gate 17 is complete when:

- Gate 11 read-only surface still validates unchanged.
- Gate 17 scaffold generation succeeds.
- Gate 17 scaffold validation succeeds.
- The guarded endpoint health reports browser scaffold allowance while preserving authorization/provenance/security-audit/finalization flags.
- Manual browser submission can mutate an authorized review action through `POST /review/update`.
- Browser observer submission is denied by the guarded endpoint.
- Browser missing request ID submission is rejected before mutation.
- Denied/rejected browser requests write security-denial audit events.
- Authorized browser mutation writes normal review mutation audit/provenance.
- Finalization remains disabled.

## Proposed Validation Commands

From `backend`:

```bash
python -m app.scripts.run_gate17_browser_action_scaffold
```

Dry run:

```bash
python -m app.scripts.run_gate17_browser_action_scaffold --dry-run
```

Manual local browser smoke:

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

Submit authorized reviewer actions through the scaffold. Do not edit review JSON directly. The poor computer will not enjoy cleaning that up.

## Expected Generated Artifacts

| Artifact | Purpose |
|---|---|
| `kbs/review/kb_draft_review_manifest.gate17_browser.json` | Gate 17 browser scaffold manifest copy |
| `kbs/manifests/kb_draft_review_action_scaffold.gate17.html` | Browser action scaffold |
| `kbs/manifests/kb_draft_review_export.gate17_browser.md` | Guarded-regenerated export after manual browser mutation |
| `kbs/manifests/kb_draft_review_surface.gate17_browser.html` | Guarded-regenerated surface after manual browser mutation |
| `kbs/audit/security_denials.gate17.jsonl` | Browser-denial security audit output |

## Non-Negotiable Guardrails

- Browser code may call the guarded endpoint only.
- Browser code must not write files.
- Browser code must not modify review JSON directly.
- Gate 11 read-only surface must remain read-only.
- Finalization must remain disabled.
- Server-side auth/provenance/audit remains authoritative.

## Recommended Follow-On

After Gate 17 completes, the next production-hardening slice should be:

**Gate 17A — OIDC Adapter Skeleton**

Gate 17A should add an adapter behind the existing `AuthAdapter` protocol without enabling it by default.
