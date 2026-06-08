# Gate 21V — Genti Review Workflow Local Demo Polish Checkpoint

## Gate

Gate 21V — Genti Review Workflow Local Demo Polish

## Change Type

Runtime prototype polish.

## Branch

`gate-21v-demo-polish`

## Files Changed

- `scripts/genti_demo.sh`
- `scripts/verify_gate_21v_genti_demo_polish.sh`

## Scope

Gate 21V improves local operator ergonomics for the Genti demo CLI without changing the seeded workflow data model.

## CLI Changes

Added commands:

```bash
bash scripts/genti_demo.sh quiet
bash scripts/genti_demo.sh show-files
bash scripts/genti_demo.sh clean
```

Existing commands remain supported:

```bash
bash scripts/genti_demo.sh prepare
bash scripts/genti_demo.sh query
bash scripts/genti_demo.sh reports
bash scripts/genti_demo.sh summary
bash scripts/genti_demo.sh all
```

## Behavior

- `quiet` runs the full demo path and prints only the compact summary.
- `show-files` prints the expected generated database and report paths.
- `clean` removes the default generated artifact directory.

## Verification

Verifier:

```bash
bash scripts/verify_gate_21v_genti_demo_polish.sh
```

The verifier checks:

- quiet mode produces the compact summary
- quiet mode suppresses noisy verifier output
- generated database exists
- generated reports exist
- show-files lists the database and five reports
- clean removes the default artifact directory

## Expected Output

```text
Gate 21V demo polish validation passed
quiet_summary_present: 1
quiet_noise_suppressed: 1
show_files_paths_present: 6
generated_reports_present: 5
clean_removed_default_artifacts: 1
```

## Runtime Artifact Policy

Generated files under:

```text
artifacts/genti_review_workflow/
```

are runtime artifacts and should not be committed.

## Boundary

This gate changes local CLI ergonomics only. It does not add production Oracle objects, APEX pages, PDF extraction, Web-site import, automated mismatch generation, or role integration.

## Current Status

Gate 21V is ready for local pull-and-run verification.
