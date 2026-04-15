# Upgrade Impact Tool — Phase 4 Completion Artifact

**Date:** 2026-04-15  
**Status:** Complete  
**Scope:** Analysis staleness, controlled refresh, delta summary, audit, lineage, and admin inspection

## Objective

Phase 4 introduced deterministic post-analysis change handling for completed analyses.

This phase expanded the system from one-time analysis execution into a bounded refresh-aware workflow that can:

- detect when an existing analysis is stale
- preserve prior analyses as historical records
- create a refreshed successor analysis
- summarize what changed between runs
- surface lineage and audit transitions
- support bounded administrative inspection

The phase preserved the synchronous MVP architecture and did not introduce asynchronous orchestration, workflow engines, or redesign of current ownership boundaries.

## Completed Work Packages

### WP-01 — Change Detection Engine

Implemented baseline source fingerprinting for analysis runs.

Delivered:
- `previous_analysis_id` on `analysis_runs`
- `snapshot_hash` on `analysis_runs`
- `analysis_input_hash` on `analysis_runs`
- `stale_reason` on `analysis_runs`
- `stale_detected_utc` on `analysis_runs`
- baseline hash backfill for existing analysis rows
- deterministic KB catalog hash generation from current KB article set
- deterministic analysis input hash generation from snapshot hash + KB catalog hash

Result:
- each analysis run now records the source-state fingerprint needed for later staleness evaluation

### WP-02 — Staleness Evaluation

Implemented deterministic staleness evaluation for existing analyses.

Delivered:
- `POST /api/v1/analyses/{analysis_id}/evaluate-staleness`
- comparison of recorded vs current:
  - snapshot hash
  - KB catalog hash
  - analysis input hash
- stale triggers:
  - `SNAPSHOT_CHANGED`
  - `KB_CATALOG_CHANGED`
  - `ANALYSIS_INPUT_CHANGED`
- stale transition persistence through `state_transitions`

Result:
- analyses can now be explicitly evaluated and marked `STALE` without mutating findings or replacing historical runs

### WP-03 — Controlled Refresh Execution

Implemented bounded refresh execution from stale analyses.

Delivered:
- `POST /api/v1/analyses/{analysis_id}/refresh`
- refresh allowed only from `STALE`
- new analysis run creation with:
  - new `analysis_id`
  - same customer/environment context
  - active snapshot reuse
  - current KB catalog hash
  - new `analysis_input_hash`
  - lineage link through `previous_analysis_id`
- normal analysis execution reused for refresh runs
- prior analysis preserved unchanged

Result:
- refresh now produces a successor run rather than mutating or overwriting the original analysis

### WP-04 — Delta Summary Generation

Implemented deterministic run-to-run delta summarization.

Delivered:
- `GET /api/v1/analyses/{analysis_id}/delta-summary`
- delta comparison against `previous_analysis_id`
- summary outputs:
  - new findings count
  - resolved findings count
  - updated findings count
  - unchanged findings count
  - new KB articles represented
  - updated KB articles represented
  - impacted applications
  - human-readable summary lines
- analysis overview rendering for refreshed analyses

Result:
- refreshed analyses can now explain what changed relative to the prior run

### WP-06 — Audit and Lineage Tracking

Implemented analysis audit visibility and lineage chain retrieval.

Delivered:
- recursive lineage retrieval from current analysis back through prior analyses
- transition retrieval across the lineage set
- `GET /api/v1/analyses/{analysis_id}/audit`
- analysis overview rendering of:
  - lineage chain
  - transition history

Result:
- refreshed and stale analyses are now inspectable as part of a deterministic lineage/audit surface

### WP-05 — Administrative Inspection Views

Implemented bounded admin inspection UI for stale and refreshed analyses.

Delivered:
- dashboard extension with:
  - `previous_analysis_id`
  - `stale_reason`
  - `stale_detected_utc`
- `/admin/inspection` route
- stale analyses inspection section
- refreshed analyses inspection section
- on-demand audit load from admin view
- dashboard entry point into admin inspection

Result:
- operators now have a minimal inspection surface for stale and refreshed analyses without adding a separate admin subsystem

## Final Functional Posture at End of Phase 4

The system now supports the full bounded stale/refresh loop:

1. complete an analysis
2. record deterministic source-state fingerprints
3. evaluate whether the analysis is stale
4. mark it stale when source inputs changed
5. create a refreshed successor analysis
6. compare successor to predecessor
7. inspect lineage and transitions
8. review stale/refreshed runs from a bounded admin inspection page

## Architectural Notes

Phase 4 preserved the intended MVP architecture:

- no workflow engine added
- no background job orchestration added
- no hidden asynchronous processing model introduced
- no redesign of current route structure
- no replacement of the synchronous execution path
- prior analyses remain immutable historical records
- refresh produces successor runs rather than in-place mutation

## Key Invariants Preserved

- completed analyses are not overwritten
- stale marking is explicit and deterministic
- refresh requires a stale predecessor
- lineage is explicit through `previous_analysis_id`
- audit transitions remain queryable
- dashboard remains the landing surface
- analysis overview remains the primary analysis work surface
- admin inspection remains bounded and read-oriented

## Known Non-Goals / Deferred Work

Not implemented in Phase 4:

- automatic scheduled stale evaluation
- automatic refresh execution
- approval workflow for refresh
- delta visualization beyond summary counts/notes
- side-by-side finding diff UI
- bulk stale/refresh operations
- notification delivery
- advanced admin controls beyond inspection
- lineage graph visualization

## Recommended Start for Phase 5

Begin with one of:

1. side-by-side analysis comparison and richer delta inspection
2. bounded operator controls for refresh governance
3. automated stale evaluation policy with explicit user-triggered execution retained

## Bottom Line

Phase 4 successfully converted analysis results from one-time outputs into refresh-aware, lineage-preserving operational records.

The system can now detect stale analyses, create deterministic successor runs, summarize changes, and expose audit/lineage/admin inspection surfaces without violating the current MVP architecture.