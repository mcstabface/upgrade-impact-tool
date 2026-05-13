# Gate 17I Disabled Adapter Selection Smoke Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Disabled Adapter Selection Smoke  
Status: Proposed  
Generated: 2026-05-13

## Purpose

Gate 17I adds a disabled smoke path for explicit adapter selection.

This gate does not change the live guarded endpoint default. It verifies that disabled OIDC adapter selection denies safely and writes a valid security-denial audit event.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/disabled_adapter_selection_smoke.py` | Disabled adapter selection smoke helper |
| `backend/app/scripts/validate_disabled_adapter_selection_smoke.py` | Validation cases |
| `backend/app/scripts/run_gate17i_disabled_adapter_selection_smoke.py` | Gate runner |

## Scope

In scope:

- reject unsupported adapter names,
- require policy path for local-policy smoke selection,
- select disabled OIDC adapter in smoke-only path,
- deny disabled OIDC selection,
- write a mapped security-denial audit event,
- validate the temporary audit event.

Out of scope:

- live endpoint adapter switching,
- production token use,
- action authorization,
- finalization.

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate17i_disabled_adapter_selection_smoke
```

Expected output:

```text
[gate17i:adapter-selection] OK
[gate17i:adapter-selection] unsupported_adapter=fail_closed
[gate17i:adapter-selection] local_policy_requires_policy_path=true
[gate17i:adapter-selection] oidc_disabled=selected_and_denied
[gate17i:adapter-selection] security_audit=valid
[gate17i:adapter-selection] authorization=unchanged_disabled
```

Recommended next gate: **Gate 17J — Explicitly Configured OIDC Endpoint Integration Design**.
