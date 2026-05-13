# Gate 17I Disabled Adapter Selection Smoke Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: Disabled Adapter Selection Smoke  
Status: Complete  
Generated: 2026-05-13

## Purpose

Gate 17I adds a disabled smoke path for explicit adapter selection.

This gate does not change the live guarded endpoint default. It verifies that disabled OIDC adapter selection denies safely and writes a valid security-denial audit event.

## Files Added

| File | Purpose |
|---|---|
| `backend/app/scripts/disabled_adapter_selection_smoke.py` | Disabled adapter selection smoke helper |
| `backend/app/scripts/validate_disabled_adapter_selection_smoke.py` | Validation cases |
| `backend/app/scripts/run_gate17i_disabled_adapter_selection_smoke.py` | Gate runner |
| `docs/checkpoints/Gate 17I Disabled Adapter Selection Smoke Build Plan.md` | Build plan |

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate17i_disabled_adapter_selection_smoke
```

## Local Validation Result

```text
[gate17i:adapter-selection] OK
[gate17i:adapter-selection] unsupported_adapter=fail_closed
[gate17i:adapter-selection] local_policy_requires_policy_path=true
[gate17i:adapter-selection] oidc_disabled=selected_and_denied
[gate17i:adapter-selection] security_audit=valid
[gate17i:adapter-selection] authorization=unchanged_disabled
[gate17i] Pipeline complete
[gate17i] Disabled adapter selection smoke remains non-authorizing and audit-valid
```

## Coverage

Gate 17I validates:

- unsupported adapter name fails,
- local-policy smoke selection requires an explicit policy path,
- disabled OIDC adapter selection succeeds only in the smoke path,
- disabled OIDC selection denies,
- a mapped security-denial audit event is written,
- the temporary audit event validates,
- the result remains non-authorizing.

## Completion

Gate 17I is complete for the disabled adapter-selection smoke slice.

Recommended next gate: **Gate 17J — Explicitly Configured OIDC Endpoint Integration Design**.
