# Gate 17M Adapter Config Existing Mutation Smoke Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Adapter Config Health With Existing Mutation Smoke  
Status: Proposed  
Generated: 2026-05-13

## Purpose

Gate 17M checks that adapter config health reporting does not disturb the existing guarded review update smoke path.

## File

| File | Purpose |
|---|---|
| `backend/app/scripts/run_gate17m_adapter_config_existing_mutation_smoke.py` | Starts the server with adapter config health enabled and runs the existing smoke checks |

## Validation Command

From `backend`:

```bash
python -m app.scripts.run_gate17m_adapter_config_existing_mutation_smoke
```

Expected final output:

```text
[gate17m] Pipeline complete
[gate17m] Adapter config health surface coexists with existing local-policy mutation path
```

## Completion Criteria

- health reports adapter config details,
- live adapter remains local policy,
- authorized mutation still succeeds,
- denied and missing-provenance requests still fail safely,
- review and audit validators pass.

Recommended next gate: **Gate 18A — Embedding Manifest and Vector Store Design**.
