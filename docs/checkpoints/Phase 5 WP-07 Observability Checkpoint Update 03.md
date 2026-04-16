# Upgrade Impact Tool — Phase 5 WP-07 Observability Checkpoint Update 03

**Date:** 2026-04-16  
**Status:** Checkpoint Update Complete  
**Phase:** Phase 5  
**Work Package:** WP-07 Pilot Readiness and Observability

## Objective

This checkpoint update extends the pilot usage summary with stale-to-refresh turnaround time.

The goal of this slice was to add one more truthful pilot-readiness metric using data the system already captures, without fabricating frontend timing or introducing a larger telemetry model.

## Scope Completed in This Update

### 1. Stale-to-Refresh Turnaround Metric

Delivered:
- stale-to-refresh turnaround added to `pilot_usage_metrics`
- metric derived from:
  - stale analyses with `stale_detected_utc`
  - refreshed analyses with `previous_analysis_id`
  - refreshed analysis `started_utc`

Result:
- admins can now see how long stale analyses typically wait before refresh begins

### 2. Refresh Turnaround Repository Support

Delivered:
- observability repository query for stale-analysis to refresh-analysis linkage
- refresh turnaround rows now retrieved directly from current analysis truth

Result:
- turnaround metric is computed from persisted lineage/state data rather than inferred from guesswork

### 3. Pilot Usage Summary Expansion

Delivered:
- `Pilot Usage Summary` now includes:
  - intake completion rate
  - blocked validation rate
  - time to first successful analysis
  - stale-to-refresh turnaround
  - review item creation rate
  - export usage rate

Result:
- pilot readiness view now covers both intake/analysis flow and stale/refresh operational responsiveness

### 4. Admin Inspection Integration

Delivered:
- stale-to-refresh turnaround card added to admin inspection pilot usage summary
- previously delivered operational and observability sections remained intact

Result:
- admins can assess refresh responsiveness without leaving the bounded observability workflow

## Verified Behaviors

### Observability API
Verified:
- `GET /api/v1/observability/summary` with `X-User-Role: ADMIN` returns:
  - `pilot_usage_metrics`
  - metric entry labeled `Stale-to-Refresh Turnaround`

### Admin Inspection UI
Verified:
- `Pilot Usage Summary` renders the new turnaround metric card
- all previously delivered pilot usage cards still render correctly
- existing observability sections still work
- stale/refreshed inspection still works
- audit inspection still works

### Metric Correctness
Verified:
- metric is computed from actual stale detection and refresh-start timestamps
- current seeded data produces a real value rather than `N/A`

## Architectural Notes

This update preserved bounded WP-07 scope:

- no frontend interaction timing capture
- no external analytics platform
- no session model
- no speculative timing inference
- no new persistence model for observability summaries

The metric is derived directly from existing system truth.

## Invariants Preserved

- backend remains source of truth
- refresh lineage remains authoritative
- observability remains admin-bounded
- metrics remain explicitly derived
- no hidden telemetry behavior was introduced

## Deferred / Not Yet Implemented

Still not completed in WP-07:

- average time spent on results overview
- sponsor demo metrics package
- per-role usage breakdown
- exportable observability reports
- scheduled pilot-readiness digest
- request/error trend summaries

## Outcome

WP-07 now provides a more complete pilot-readiness view by covering both:

- how users progress through intake and analysis
- how quickly operators react when analyses become stale

This improves operational visibility while preserving project truth boundaries.

## Recommended Next Step

Proceed only if there is a clear reason to extend WP-07 further.

The next reasonable decision is one of:

- stop WP-07 here because current pilot-readiness visibility is sufficient for MVP scope, or
- add a small, explicit frontend interaction timing foundation before attempting `average time spent on results overview`

Do not fake results-overview timing from backend request counts or page loads.

## Bottom Line

WP-07 now measures not just whether stale analyses exist, but whether anyone actually does something about them.

A modest but meaningful victory over operational entropy.