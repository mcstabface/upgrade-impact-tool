# Gate 17K Endpoint Adapter Selection Config Skeleton Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Endpoint Adapter Selection Config Skeleton  
Status: Proposed  
Generated: 2026-05-13

## Purpose

Gate 17K adds config loading and validation for future endpoint adapter selection.

This gate does not wire the config into the live guarded endpoint. The default remains `local_policy`.

## Files

| File | Purpose |
|---|---|
| `backend/app/scripts/endpoint_adapter_selection_config.py` | Config dataclass, loader, and validator |
| `backend/app/scripts/validate_endpoint_adapter_selection_config.py` | Validation cases |
| `backend/app/scripts/run_gate17k_adapter_selection_config_skeleton.py` | Gate runner |

## Scope

In scope:

- missing config defaults to local policy,
- unsupported adapter fails,
- OIDC selected without allow flag fails,
- OIDC selected with allow flag validates structurally,
- endpoint integration remains disabled.

Out of scope:

- live endpoint wiring,
- enabling OIDC,
- production token use,
- finalization.

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate17k_adapter_selection_config_skeleton
```

Expected output:

```text
[gate17k:adapter-config] OK
[gate17k:adapter-config] missing_config=local_policy_default
[gate17k:adapter-config] unknown_adapter=fail_closed
[gate17k:adapter-config] oidc_without_allow=fail_closed
[gate17k:adapter-config] endpoint_integration=not_enabled
```

Recommended next gate: **Gate 17L — Guarded Endpoint Adapter Config Read-Only Health Surface**.
