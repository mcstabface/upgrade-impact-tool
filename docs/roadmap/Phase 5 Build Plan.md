Phase 5 Build Plan v1

System: Upgrade Impact Analysis Tool
Purpose: Harden the system for sustained real-world use
Goal: Improve performance, usability, governance, and production readiness without changing core truth models

1. Phase 5 Objectives

By the end of Phase 5, the system should support:

fast enough response times
clean report/export generation
guided onboarding
role-safe usage
notification of important changes
reliable operations under normal team usage

This phase is about operational maturity.

2. Exit Criteria

Phase 5 is complete when:

Primary user paths feel polished and low-friction
Reports can be exported cleanly
Role boundaries are enforced
Important stale/review states can notify users
Performance is acceptable for pilot usage
Error states are understandable and recoverable
System can support a controlled production pilot
3. Phase 5 Scope

This phase includes seven work packages:

WP-01 Export and Reporting Hardening
WP-02 Performance and Query Optimization
WP-03 Onboarding and Guided UX
WP-04 Role-Based Access Control
WP-05 Notifications and Scheduling
WP-06 Reliability and Recovery Hardening
WP-07 Pilot Readiness and Observability
WP-01 — Export and Reporting Hardening
Goal

Turn the in-app truth into shareable outputs that preserve provenance and readability.

Required Deliverables

Support export of:

full report PDF
application-only PDF
review queue CSV/XLSX
technical appendix export
admin/audit JSON export where permitted
Export Requirements

Every export must preserve:

assumptions
missing inputs
derived risks
finding statuses
KB article numbers
KB titles
source links

The same evidence-visible requirement applies here as in the UI. If an exported finding loses provenance, the export is lying on behalf of the system. The UI guidance already makes clear that visible evidence is the differentiator, not optional garnish.

Tasks
Backend
implement export rendering service
create PDF templates
create CSV/XLSX generation for queues
attach export metadata and content hashes
persist export events
Frontend
export modal / screen
scope selection
export history display
progress and completion states
Testing
PDF readable and complete
CSV columns consistent
exports preserve KB provenance
exports match current analysis truth
WP-02 — Performance and Query Optimization
Goal

Improve response speed without changing analysis semantics.

Focus Areas
dashboard aggregation speed
results overview query speed
finding detail retrieval speed
review queue filter performance
refresh/delta comparison speed
Constraints

No hidden caching that makes truth ambiguous.

Performance work must preserve deterministic behavior and traceability. The architecture favors boring and explicit over clever but unclear, so performance shortcuts that create stale or opaque state are not acceptable.

Tasks
Backend
add missing indexes
profile slow queries
optimize aggregation queries
introduce safe read-model materialization only if explicitly versioned
optimize delta comparison queries
Frontend
add pagination or virtualized lists where needed
reduce redundant fetches
improve loading-state handling
Testing
benchmark primary screens
ensure same inputs return same results
verify no stale-read ambiguity introduced
WP-03 — Onboarding and Guided UX
Goal

Reduce user hesitation and incomplete intake errors.

Required UX Features
guided intake helper text
“why we ask this” explanations
sample intake templates
empty-state guidance
first-run walkthrough hints
clearer blocked/unknown explanations

This is directly aligned with the UI direction to keep the product clean, simple, and trust-building rather than jargon-heavy or cluttered.

Tasks
Frontend
add inline help
add first-run walkthrough
add sample intake download
refine copy for blocked/unknown states
improve empty states
Product/Docs
create quick-start guide
create intake prep checklist
create “how to read this report” guidance
Testing
new user can complete intake with less assistance
blocked states produce recovery, not confusion
users can explain assumptions/missing inputs after first use
WP-04 — Role-Based Access Control
Goal

Enforce clean separation between normal users and admin/operators.

Required Roles
Viewer
Analyst
Reviewer
Admin

These roles were already defined in the workflow model; now they become enforcement rather than aspiration.

Required Permissions
Viewer
view results
export approved reports
Analyst
create/edit intake
start analysis
view results
Reviewer
manage review items
add comments
update review statuses
Admin
KB admin
snapshot admin
refresh admin
audit inspection
config management
Tasks
Backend
add auth middleware hooks
enforce route-level authorization
enforce export permission logic
audit permission-sensitive actions
Frontend
hide inaccessible actions
role-aware navigation
permission-denied messaging
Testing
unauthorized actions rejected
admin-only screens protected
UI does not expose disallowed controls
WP-05 — Notifications and Scheduling
Goal

Surface important operational events without requiring constant manual inspection.

Required Notification Events
analysis complete
review item assigned
review item overdue
analysis marked stale
refresh completed
blocked analysis requires action
Supported Channels v1
in-app notifications
email

Optional later:

Slack / Teams
Scheduling Scope

Minimal safe scheduling only:

daily stale scan
daily overdue review item scan
optional weekly summary

Do not overbuild “automation.” This should be bounded, explicit notification behavior, not an autonomous operations goblin.

Tasks
Backend
notification event generator
notification delivery table
email adapter
scheduler for stale/overdue scans
Frontend
in-app notification tray
notification badges
link-to-target behavior
Testing
notifications fire deterministically
duplicate notifications avoided
overdue scan works on schedule
WP-06 — Reliability and Recovery Hardening
Goal

Make failure states survivable and understandable.

Required Capabilities
recoverable background job failures
partial operation visibility
safe retry behavior
error classification
operational runbooks
Required Error Classes
validation error
source data error
ingestion error
refresh error
export error
permission error
Tasks
Backend
classify and standardize errors
add retry-safe logic for exports/refresh jobs where applicable
ensure failed refresh does not corrupt analysis lineage
add structured operational logs
Frontend
clearer recovery guidance
retry affordances where safe
stable error states
Testing
failed refresh does not overwrite prior truth
failed export visible and retryable
user-readable error messages present
WP-07 — Pilot Readiness and Observability
Goal

Prepare the system for controlled rollout and real feedback.

Required Metrics
intake completion rate
blocked validation rate
time to first successful analysis
average time spent on results overview
review item creation rate
stale-to-refresh turnaround time
export usage rate
Required Operational Views
system health summary
pilot usage dashboard
most common blocked fields
most common missing inputs
most frequent review reasons

This is where you start learning whether the product is actually working socially, not just technically.

Tasks
Backend
capture usage events
aggregate pilot metrics
expose observability endpoints
Frontend
admin observability screen
pilot usage summary cards
Product
define pilot success criteria
define feedback collection workflow
define sponsor demo metrics
Testing
usage events emitted correctly
metrics aggregate correctly
operational dashboard reflects system behavior
4. Recommended Build Order

Safest sequence:

1. Export and Reporting Hardening
2. Role-Based Access Control
3. Reliability and Recovery Hardening
4. Onboarding and Guided UX
5. Notifications and Scheduling
6. Performance and Query Optimization
7. Pilot Readiness and Observability

Why:

exports and permissions matter early
reliability before scale
guidance before broader users
notifications after roles and state rules are stable
performance tuning after actual usage paths are clearer
observability once behavior is real enough to measure
5. Concrete Task List
Backend Tasks
Implement PDF export service
Implement CSV/XLSX review queue export
Persist export metadata
Add role enforcement middleware
Add permission checks per route
Standardize error classes
Add retry-safe export and refresh jobs
Implement notification event service
Implement email delivery adapter
Implement scheduled stale/overdue scans
Optimize key dashboard/results queries
Add operational metrics event capture
Expose observability endpoints
Frontend Tasks
Build export modal/screen
Add export history display
Add role-aware navigation
Hide unauthorized actions
Add notification tray
Add onboarding hints and helper text
Add sample intake template download
Refine empty/error/blocked states
Polish results and queue interactions
Build observability/admin summary view
Docs / Product Tasks
Write quick-start guide
Write admin runbook
Write refresh recovery runbook
Write export usage guide
Define pilot success metrics
Define support/escalation process
6. Minimum Testing Scope
Backend
exports generated correctly
role enforcement correct
notifications deterministic
stale scan works
retries do not corrupt lineage
key queries meet baseline performance target
Frontend
export flow works
unauthorized controls hidden
onboarding guidance visible
notification tray usable
error recovery states understandable
Operational / End-to-End
run analysis
export report
mark analysis stale
receive notification
refresh safely
verify prior history preserved
verify access differs by role
7. What Not to Build in Phase 5

Do not build:

advanced workflow automation
AI-generated remediation advice
external ticketing integrations
multi-org federation
full enterprise SSO complexity beyond initial auth needs
semantic search over findings unless separately justified

Those are future expansion items, not hardening essentials.

8. Recommended Demo at End of Phase 5

You should be able to show:

User logs in with role-appropriate access
Creates or opens analysis
Reviews results with clear guidance
Exports a clean report
Creates and tracks review work
System marks stale after source change
User receives notification
Refresh occurs safely
Admin inspects lineage and health
Usage/operational metrics visible

That proves the system is not just functional, but pilot-ready.

9. Risks in Phase 5
Risk

Polish work expands forever.

Mitigation:

Tie all polish to measured user friction or pilot readiness
Risk

Notifications become noisy.

Mitigation:

Start with a small deterministic event set
Risk

RBAC introduces UX confusion.

Mitigation:

Hide disallowed actions and explain role boundaries simply
Risk

Performance work introduces opaque caching.

Mitigation:

Prefer explicit indexed retrieval and versioned read models only
10. Definition of Done

Phase 5 is done when:

System is export-capable
Role-safe
Notification-aware
Operationally recoverable
Usable by first pilot users without constant handholding
Observable enough to improve with evidence

At that point, the system is not just ready to show.

It is ready to live.

11. Where This Leaves Us

At this point, the design stack is complete:

Intake Contract
Change Record Schema
Report Template
UI Information Architecture
Screen Specifications
Workflow State Model
Data Model / Storage Schema
API / Service Contract
Phase 0–5 Build Plans