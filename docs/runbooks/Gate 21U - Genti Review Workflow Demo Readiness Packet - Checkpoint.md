# Gate 21U — Genti Review Workflow Demo Readiness Packet Checkpoint

## Gate

Gate 21U — Genti Review Workflow Demo Readiness Packet

## Change Type

Documentation plus verification script.

## Branch

`gate-21u-demo-readiness`

## Files Added

- `docs/runbooks/Genti Review Workflow Demo Readiness Packet.md`
- `scripts/verify_gate_21u_genti_demo_readiness.sh`

## Scope

Gate 21U adds an operator-ready packet for the local Genti review workflow demo.

The packet documents:

- pre-demo setup
- primary demo command
- individual demo commands
- verification command
- generated database path
- generated report paths
- suggested demo flow
- demo talking points
- questions to ask Genti
- cleanup command
- runtime artifact policy

## Verification

Verifier:

```bash
bash scripts/verify_gate_21u_genti_demo_readiness.sh
```

The verifier checks:

1. the readiness packet exists
2. the packet references required demo commands
3. the packet references required generated artifact paths
4. the packet includes cleanup guidance
5. the Gate 21T demo CLI verifier passes using temporary artifact paths
6. the expected generated DB and report files exist in the temp path

## Expected Output

```text
Gate 21U readiness packet content validation passed
required_terms: 15
Gate 21U demo readiness validation passed
demo_db_present: 1
report_files_present: 5
```

## Runtime Artifact Policy

The verifier uses a temporary directory for generated artifacts and removes it automatically.

The normal demo path may still create runtime artifacts under:

```text
artifacts/genti_review_workflow/
```

Those generated files should not be committed.

## Boundary

This gate does not add production Oracle objects, APEX pages, PDF extraction, Web-site import, automated mismatch generation, or role integration.

## Current Status

Gate 21U is ready for local pull-and-run verification.
