# Upgrade Impact Tool — Phase 5 WP-07 Observability Checkpoint Update 02

**Date:** 2026-04-16  
**Status:** Checkpoint Update Complete  
**Phase:** Phase 5  
**Work Package:** WP-07 Pilot Readiness and Observability

## Objective

This checkpoint update extends WP-07 from operational observability into real pilot-usage measurement.

The goal of this slice was not to build a telemetry platform or infer user behavior from unrelated system state. The goal was to establish a truthful pilot usage summary based on explicitly captured usage events.

## Scope Completed in This Update

### 1. Usage Event Capture Foundation

Delivered:
- `usage_events` persistence model
- usage event repository
- usage event service
- event indexes for query support

Result:
- the system now has an explicit substrate for pilot-readiness metrics rather than relying on indirect inference

### 2. Instrumented Usage Event Emission

Delivered event capture for:
- intake creation
- intake validation success
- intake blocked validation
- analysis start
- analysis completion
- analysis refresh creation
- export trigger events
- review item creation

Result:
- core pilot interactions now emit durable usage events that can be aggregated later

### 3. Pilot Usage Metrics in Observability Summary

Delivered:
- `pilot_usage_metrics` added to observability summary contract
- truth-derived pilot metric calculation from `usage_events`

Current metrics include:
- intake completion rate
- blocked validation rate
- time to first successful analysis
- review item creation rate
- export usage rate

Result:
- pilot usage summary now reflects actual captured behavior rather than operational guesswork

### 4. Admin Inspection Integration

Delivered:
- `Pilot Usage Summary` cards added to `AdminInspectionPage`
- existing system health, blocked fields, missing inputs, review reasons, stale analysis, refreshed analysis, and audit views remained intact

Result:
- pilot usage metrics now live inside the same bounded admin inspection workflow

### 5. Intake Submission Failure Correction

Delivered:
- corrected frontend intake service to use shared API client with role header propagation
- restored browser-based intake creation flow
- ensured usage events can be generated from normal UI-driven intake actions

Result:
- pilot usage metrics can now be driven by normal product usage rather than curl-only testing

## Verified Behaviors

### Usage Event Persistence
Verified:
- usage events persist for:
  - `INTAKE_CREATED`
  - `INTAKE_BLOCKED`
  - `INTAKE_VALIDATED`
  - `ANALYSIS_STARTED`
  - `ANALYSIS_COMPLETED`
  - `EXPORT_TRIGGERED`

### Observability API
Verified:
- `GET /api/v1/observability/summary` with `X-User-Role: ADMIN` returns:
  - `system_health_status`
  - `counts`
  - `pilot_usage_metrics`
  - `most_common_blocked_fields`
  - `most_common_missing_inputs`
  - `most_frequent_review_reasons`

### Admin Inspection UI
Verified:
- `Pilot Usage Summary` appears
- usage metric cards render correctly
- previously delivered observability sections still render correctly
- stale/refreshed inspection still works
- audit inspection still works

### Intake UI Recovery
Verified:
- browser intake flow works again after restoring role-aware API usage in the intake service
- sample intake submission can now generate pilot usage events through normal UI behavior

## Architectural Notes

This update preserved bounded WP-07 scope:

- no external telemetry platform
- no frontend clickstream capture
- no session replay
- no analytics vendor integration
- no separate observability datastore
- no speculative behavior inference

Pilot metrics are derived only from explicitly emitted application events.

## Invariants Preserved

- backend remains source of truth
- usage metrics are derived from durable events
- role enforcement remains intact
- observability remains admin-bounded
- no hidden or ambiguous telemetry layer was introduced
- current synchronous MVP model remains unchanged

## Deferred / Not Yet Implemented

Not completed in this update:

- average time spent on results overview
- stale-to-refresh turnaround time
- sponsor demo metrics package
- per-role usage breakdown
- exportable observability reports
- request/error trend metrics
- scheduled pilot-readiness digest

## Outcome

WP-07 now includes both operational observability and a first truthful pilot usage summary.

The system can now show:
- operational health
- most common blocked fields
- most common missing inputs
- most frequent review reasons
- intake completion rate
- blocked validation rate
- time to first successful analysis
- review item creation rate
- export usage rate

This materially improves pilot readiness without overbuilding observability.

## Recommended Next Step

Proceed with the next bounded WP-07 slice only after preserving this checkpoint.

The next reasonable slice is:
- add stale-to-refresh turnaround time using current refresh and staleness event/state data

Do not implement average time spent on results overview until real frontend interaction timing is explicitly captured.

## Bottom Line

WP-07 now measures actual product usage instead of staring at the database and trying to develop intuition.

A rare and welcome departure from software mysticism.