# Gate 21T — Genti Review Workflow Local Demo CLI Prototype Completion

## Status

Complete.

## Change Type

Runtime/prototype change.

## Pull Request

PR #70 — Gate 21T — Genti Review Workflow Local Demo CLI Prototype

Merged via squash commit:

```text
04ad38b7beccedc38c4a72c55ccc920b0f235319
```

## Runtime Files Added

- `scripts/genti_demo.sh`
- `scripts/verify_gate_21t_genti_demo_cli.sh`

## Documentation Added

- `docs/runbooks/Gate 21T - Genti Review Workflow Local Demo CLI Prototype - Checkpoint.md`

## Completed Scope

Gate 21T added a local CLI wrapper around the Genti review workflow prototype path.

The CLI supports:

- preparing the seeded demo database
- checking query/view output
- creating report exports
- printing a compact demo summary
- running the full local demo path

## CLI Commands

```bash
bash scripts/genti_demo.sh prepare
bash scripts/genti_demo.sh query
bash scripts/genti_demo.sh reports
bash scripts/genti_demo.sh summary
bash scripts/genti_demo.sh all
```

## Pull-and-Run Verification

Command:

```bash
bash scripts/verify_gate_21t_genti_demo_cli.sh
```

## Verified Local Output

The verifier passed from local PR branch validation before merge.

Observed output:

```text
Gate 21T demo CLI validation passed
bug_entries: 11
mismatch_flags: 11
test_required_entries: 1
bug_pdf_artifacts: 3
audit_events: 6
report_files_present: 5
```

## Runtime Artifact Policy

The CLI may create or refresh files under:

```text
artifacts/genti_review_workflow/
```

Generated DB and report files are runtime artifacts and must remain uncommitted.

## Boundary Preserved

Gate 21T does not implement:

- Oracle production schema
- APEX pages
- PDF extraction
- Web-site import
- automated mismatch generation
- role integration

## Next Gate

Recommended next gate:

Gate 21U — Genti Review Workflow Demo Readiness Packet

Recommended scope:

- operator runbook for local demo
- demo talking points using generated outputs
- list of generated files to inspect
- cleanup instructions for runtime artifacts
- pull-and-run verification

## Gate 21T Result

Gate 21T is complete and merged.
