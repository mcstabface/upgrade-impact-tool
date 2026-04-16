# Upgrade Impact Tool — Phase 5 WP-05 Notifications Checkpoint Update 02

**Date:** 2026-04-15  
**Status:** Checkpoint Update Complete  
**Phase:** Phase 5  
**Work Package:** WP-05 Notifications and Scheduling

## Objective

This checkpoint update extends the initial WP-05 in-app notification foundation with a minimal persisted notification delivery model and read-state support.

The goal of this slice was not scheduling or outbound delivery. The goal was to move notifications from purely recomputed transient output to a deterministic persisted model that can support unread counts, read state, and future duplicate suppression.

## Scope Completed in This Update

### 1. Persisted Notification Delivery Table

Delivered:
- notification delivery migration
- persisted notification row model
- active/inactive notification state
- read/unread notification state
- created/updated timestamps
- notification indexes for active retrieval

Result:
- notifications now exist as persisted delivery rows rather than only as recomputed response objects

### 2. Deterministic Notification Upsert / Deactivation

Delivered:
- deterministic upsert behavior for:
  - stale analyses
  - overdue review items
- deactivation behavior when previously active notification conditions no longer apply

Result:
- notification persistence remains derived from trusted system truth instead of creating a second notification interpretation model

### 3. Read-State Support

Delivered:
- `is_read` on notification items
- unread active notification count
- mark-read endpoint
- dashboard integration for mark-read interaction

Result:
- users can now distinguish unread from previously seen active notifications

### 4. Dashboard Read-State UX

Delivered:
- expanded tray shows unread/read state
- unread items expose `Mark Read`
- mark-read action refreshes tray data
- unread count updates after read action

Result:
- in-app notifications now support a real minimal interaction loop rather than permanent perpetual unread state

## Verified Behaviors

### Notification Read API
Verified:
- `GET /api/v1/notifications` returns:
  - `unread_count`
  - `items`
  - `items[*].is_read`
- `PATCH /api/v1/notifications/{notification_id}/read` returns:
  - `notification_id`
  - `is_read = true`
  - `updated_utc`

### Read-State Transition
Verified:
- initial state showed two unread notifications
- marking `overdue-review-3` as read succeeded
- follow-up notification fetch showed:
  - unread count reduced from 2 to 1
  - read notification remained active and visible
  - chosen notification returned `is_read = true`

### Dashboard Recovery After Repository Fix
Verified:
- notification repository list-expansion fix resolved the prior internal error condition
- dashboard continued loading successfully after the fix
- persisted notification state did not break dashboard summary loading

## Architectural Notes

This update preserved bounded WP-05 scope:

- in-app notifications only
- no scheduler
- no email delivery
- no weekly summary job
- no external notification transport
- no full notification center subsystem
- no per-user routing model

Persistence was introduced only to support:
- deterministic delivery records
- unread counts
- read state
- future suppression/history possibilities

Notification generation still derives from existing trusted system truth:
- stale analyses
- overdue review items

## Invariants Preserved

- backend remains source of truth for notification content
- notification rows are derived from existing analysis/review truth, not parallel inference
- current synchronous MVP execution path remains intact
- notification persistence remains bounded and additive
- no redesign of dashboard routing or analysis/review workflows was introduced

## Deferred / Not Yet Implemented

Not completed in this update:

- notification dismissal
- archived notification history views
- per-user notification ownership
- role-filtered delivery
- scheduled stale scans
- scheduled overdue review scans
- email delivery
- weekly summary digest
- notification preference settings
- advanced duplicate suppression rules beyond deterministic delivery-row identity

## Outcome

This update makes WP-05 materially more real.

The system now has:
- persisted notification delivery rows
- unread counts based on stored state
- read/unread transitions
- continued deterministic derivation from trusted application truth

This is enough to support a legitimate in-app notification foundation without prematurely dragging in scheduling or external delivery complexity.

## Recommended Next Step

Proceed with the next bounded WP-05 slice only after preserving this checkpoint.

The next reasonable decision point is:
- determine whether notification dismissal is actually needed before any scheduler or email work begins

If scheduling is pursued later, it should build on this persisted notification foundation rather than bypass it.

## Bottom Line

WP-05 notifications are now more than a polite hallucination.

The app can remember that it already warned you.