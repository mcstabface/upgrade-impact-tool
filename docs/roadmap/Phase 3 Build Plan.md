Phase 3 Build Plan v1

System: Upgrade Impact Analysis Tool
Purpose: Convert findings into actionable work items with clear ownership and traceable status progression
Goal: Establish a controlled review workflow that turns analysis into execution

1. Phase 3 Objectives

By the end of Phase 3, the system should support this workflow:

User identifies finding
→ creates review item
→ assigns owner
→ tracks progress
→ records comments
→ resolves or defers item
→ maintains audit history

This is the first phase where the system directly supports delivery teams.

2. Exit Criteria

Phase 3 is complete when:

User can create review items from findings
Review items can be assigned to owners
Review items can move through defined status transitions
Review queue displays actionable work items
Comments can be recorded on review items
Audit history records all transitions
Blocked and overdue items are visible
Review items remain linked to original findings

If work cannot be tracked from finding to closure, the phase is not done.

3. Workflow Model
Review Item Lifecycle
OPEN
→ IN_PROGRESS
→ RESOLVED

or

OPEN
→ IN_PROGRESS
→ DEFERRED
Allowed Transitions
OPEN → IN_PROGRESS
IN_PROGRESS → RESOLVED
IN_PROGRESS → DEFERRED
DEFERRED → IN_PROGRESS
Invalid Transitions
RESOLVED → OPEN
DEFERRED → OPEN

These must be rejected at the service layer.

4. Phase 3 Scope

This phase includes six work packages:

WP-01 Review Item Creation
WP-02 Review Queue
WP-03 Assignment and Ownership
WP-04 Commenting and Activity Tracking
WP-05 Status Transitions and Validation
WP-06 Operational Visibility and Alerts
WP-01 — Review Item Creation
Goal

Allow users to convert findings into actionable work.

Required Behavior

A review item must:

reference a finding
include a reason for review
include assigned owner
include due date
inherit context from finding
Required Fields
review_item_id
finding_id
review_reason
assigned_owner_user_id
due_date
review_status
created_utc
created_by_user_id
Deliverables
Backend

Implement:

POST /review-items
GET /review-items/{id}
Frontend

Implement:

Create Review Item action
Review item form
Validation messaging
Testing
Review item links to finding
Missing owner blocks creation
Missing reason blocks creation
Creation event recorded in audit log
WP-02 — Review Queue
Goal

Provide a focused operational work list.

Required Behavior

Queue must display:

Review Item
Application
Finding Headline
Owner
Status
Due Date
Severity
KB Reference
Required Sorting

Default order:

BLOCKED
OVERDUE
OPEN
IN_PROGRESS
DEFERRED
RESOLVED

Within status:

Due date ascending
Severity descending
Deliverables
Backend

Implement:

GET /review-items
Frontend

Implement:

Review Queue screen
Filtering controls
Sorting controls
Status badges
Testing
Queue shows all review items
Sorting works correctly
Filtering works correctly
Overdue items highlighted
WP-03 — Assignment and Ownership
Goal

Ensure accountability is explicit.

Required Behavior

Every review item must have:

Assigned owner
Due date
Status
Assignment Rules
Owner required at creation
Owner can be reassigned
Assignment change logged
Deliverables
Backend

Implement:

PATCH /review-items/{id}
Frontend

Implement:

Owner selector
Due date editor
Reassignment confirmation
Testing
Owner change recorded in audit log
Due date change recorded
Invalid owner rejected
WP-04 — Commenting and Activity Tracking
Goal

Capture context and decisions without external tools.

Required Behavior

Users must be able to:

Add comment
View comment history
See timestamp and author
Required Fields
comment_id
review_item_id
comment_text
created_by_user_id
created_utc
Deliverables
Backend

Implement:

POST /review-items/{id}/comments
GET /review-items/{id}/comments
Frontend

Implement:

Comment thread component
Add comment input
Activity timeline
Testing
Comment persists correctly
Comment author recorded
Comment timestamp recorded
Comment order correct
WP-05 — Status Transitions and Validation
Goal

Prevent workflow chaos.

Required Behavior

Status transitions must:

Follow allowed transitions only
Reject invalid transitions
Log all transitions
Required Rules
Valid transitions
OPEN → IN_PROGRESS
IN_PROGRESS → RESOLVED
IN_PROGRESS → DEFERRED
DEFERRED → IN_PROGRESS
Required validation
RESOLVED requires resolution note
DEFERRED requires defer reason
Deliverables
Backend

Implement:

Status transition validator
Transition logging
Frontend

Implement:

Status change controls
Transition confirmation dialog
Validation messaging
Testing
Invalid transitions rejected
Valid transitions succeed
Transition logged in audit trail
Resolution note required
WP-06 — Operational Visibility and Alerts
Goal

Make risk visible without manual inspection.

Required Behavior

System must identify:

Overdue review items
Blocked review items
High-severity open items
Unassigned items
Required Views
A. Review Queue Indicators
Overdue badge
Blocked badge
High severity badge
B. Dashboard Alerts
Overdue items count
Blocked items count
Unassigned items count
Deliverables
Backend

Implement:

Overdue detection logic
Blocked detection logic
Alert aggregation queries
Frontend

Implement:

Alert badges
Dashboard alert panel
Queue highlighting
Testing
Overdue items flagged correctly
Blocked items flagged correctly
Unassigned items flagged correctly
Dashboard alert counts accurate
5. Recommended Build Order

Safest sequence:

1 WP-01 Review Item Creation
2 WP-05 Status Transitions and Validation
3 WP-02 Review Queue
4 WP-03 Assignment and Ownership
5 WP-04 Commenting and Activity Tracking
6 WP-06 Operational Visibility and Alerts

Reason:

Create work → enforce rules → display queue → manage ownership → track context → surface risk

6. Concrete Task List
Backend Tasks
Create review_items table
Create review_comments table
Implement review item creation endpoint
Implement review queue query
Implement status transition validator
Implement assignment update endpoint
Implement comment endpoints
Implement overdue detection logic
Implement alert aggregation queries
Implement audit logging for all changes
Frontend Tasks
Create review item form
Create review queue page
Create owner selector component
Create due date picker
Create comment thread component
Create status transition controls
Create alert badge component
Highlight overdue items
Highlight blocked items
Documentation Tasks
Document review workflow rules
Document status transition rules
Document assignment responsibilities
Document review queue sorting rules
Document audit logging behavior
7. Minimum Testing Scope
Backend
Review item creation deterministic
Invalid transitions rejected
Transition logging works
Assignment changes recorded
Comment persistence works
Overdue detection accurate
Frontend
Review queue renders correctly
Filtering works
Assignment updates reflected
Comments display correctly
Status changes reflected
Overdue items highlighted
End-to-End
Create review item
Assign owner
Add comment
Change status
Resolve item
Verify audit history
8. What Not to Build in Phase 3

Do not build:

Notification engine
Email integration
Slack integration
Escalation workflows
Bulk assignment tools
Multi-team routing logic
External ticketing integration

Those belong in Phase 5 or later.

Right now we are building:

controlled work tracking tied to findings

Not a full enterprise workflow system.

9. Recommended Demo at End of Phase 3

You should be able to show:

Open finding detail
Create review item
Assign owner
Set due date
Add comment
Change status to IN_PROGRESS
Resolve item
Show audit history
Show overdue alert on dashboard

That demo proves the system supports real operational work.

10. Risks in Phase 3
Risk

Workflow becomes too flexible.

Mitigation:

Enforce transition rules strictly
Reject invalid transitions
Log every state change
Risk

Review queue becomes cluttered.

Mitigation:

Default sorting by risk and urgency
Clear filtering controls
Highlight overdue items
Risk

Ownership becomes ambiguous.

Mitigation:

Require owner at creation
Track assignment changes
Surface unassigned items
11. Definition of Done

Phase 3 is done when:

Findings can be converted into review items
Review items have owners and due dates
Status transitions are enforced
Comments can be recorded
Queue displays actionable work
Overdue items are visible
Audit history records all actions

At that point, the system is no longer just an analysis tool.

It is an operational tool.