# Upgrade Impact Tool — Phase 5 WP-06 Reliability Checkpoint Artifact

**Date:** 2026-04-15  
**Status:** Checkpoint Complete  
**Phase:** Phase 5  
**Work Package:** WP-06 Reliability and Recovery Hardening

## Objective

WP-06 introduced the first bounded reliability and recovery hardening layer for the Upgrade Impact Tool.

The goal of this checkpoint was not full resilience architecture. The goal was to improve failure handling on the current synchronous MVP path by standardizing backend error payloads, surfacing actionable recovery guidance, and adding safe manual retry behavior on key read-heavy screens.

## Completed Scope

### 1. Standardized Backend Error Payloads

Delivered:
- centralized backend application error model
- centralized FastAPI exception handling for:
  - application errors
  - HTTP exceptions
  - validation errors
  - unexpected exceptions
- normalized error payload shape containing:
  - `error_class`
  - `message`
  - `recovery_guidance`
  - `retryable`

Result:
- backend now emits consistent error payloads instead of mixed raw exception output and route-specific strings

### 2. Error Classification

Implemented error classes include:
- `VALIDATION_ERROR`
- `PERMISSION_ERROR`
- `SOURCE_DATA_ERROR`
- `REFRESH_ERROR`
- `EXPORT_ERROR`
- `INTERNAL_ERROR`

Result:
- failures are now classified into predictable categories that frontend surfaces can render consistently

### 3. Safer Analysis Refresh / Export Failure Handling

Delivered:
- analysis refresh failures now return structured error responses
- analysis export failures now return structured error responses
- application export failures now return structured error responses
- review queue export failures now return structured error responses

Result:
- raw backend exception content is no longer the default user-facing failure mode on these paths
- recovery guidance now explains how to retry or return safely

### 4. Frontend Recovery Messaging

Delivered:
- shared frontend API client now parses structured backend error payloads
- frontend error rendering now separates:
  - primary message
  - recovery guidance
- generic backend-reachability failures now return a readable recovery message

Result:
- users now see understandable recovery instructions instead of low-quality raw request failure text

### 5. Safe Retry Affordances

Delivered:
- explicit retry control on analysis overview load failure
- explicit retry control on review queue load failure
- retry remains manual and user-initiated
- retry is only exposed on safe read/reload surfaces

Result:
- users can recover from temporary backend outages without navigating away or refreshing blindly

## Verified Behaviors

### Permission Error Payload
Verified:
- admin-only audit access as viewer returns structured payload with:
  - `error_class = PERMISSION_ERROR`
  - readable message
  - recovery guidance
  - retryable flag

### Validation Error Payload
Verified:
- invalid intake creation request returns structured payload with:
  - `error_class = VALIDATION_ERROR`
  - readable message
  - recovery guidance
  - validation details list

### Export Survival
Verified:
- review queue CSV export still succeeds after reliability changes
- export response remains `200 OK`
- export content remains valid

### Frontend Retry Behavior
Verified:
- when backend is unavailable, review queue shows:
  - readable failure title
  - readable primary message
  - recovery guidance
  - retry button
- when backend returns, retry successfully reloads review queue

Verified:
- when backend is unavailable, analysis overview shows:
  - readable failure title
  - readable primary message
  - recovery guidance
  - retry button
- when backend returns, retry successfully reloads analysis overview

## Architectural Notes

WP-06 preserved current MVP architecture:

- no background retry jobs
- no asynchronous queue-based recovery
- no hidden automatic retry loops
- no circuit breaker subsystem
- no persistent retry scheduler
- no redesign of synchronous request flow
- no new workflow system

Reliability hardening was added directly to:
- backend exception boundaries
- selected export/refresh route handling
- frontend API client parsing
- selected read-heavy UI screens

## Invariants Preserved

- retries remain explicit and user-initiated
- refresh/export paths remain synchronous
- failure handling does not mutate prior persisted state unless the original action succeeded
- prior analysis truth remains preserved when refresh fails
- export/reporting surfaces remain additive and bounded
- backend remains source of truth for error classification
- frontend recovery messaging reflects backend guidance instead of inventing separate failure semantics

## Deferred / Not Yet Implemented

Not completed in this checkpoint:
- automatic retry for safe operations
- retry counters / exponential backoff
- persistent failure event logging for operators
- structured UI error panels for every page
- safe retry on all mutation flows
- stale session / offline-aware handling
- health-aware bannering across the application
- backend dependency health fan-out
- recovery flows for every export/report route
- recovery checkpoint UI for in-progress multi-step actions

## Outcome

WP-06 established the first real reliability and recovery layer for the Upgrade Impact Tool.

The system now provides:
- predictable backend error contracts
- actionable frontend recovery messaging
- bounded, safe retry behavior on critical load paths

This materially improves operability without violating the current synchronous MVP path or introducing architecture beyond present project scope.

## Recommended Next Step

Proceed with the next bounded WP-06 slice only after preserving this checkpoint.

The next reasonable slice is:
- extend safe retry affordances to additional read-only / export-adjacent surfaces where retry is unambiguous and does not risk duplicate mutation.

## Bottom Line

WP-06 now has a real foundation.

Failures are more understandable, recovery guidance is explicit, and the user is no longer left to divine system state from a blank wall and a browser refresh button.