Interaction Flow and Workflow State Model v1

System: Upgrade Impact Analysis Tool
Purpose: Define the lifecycle states, transitions, triggers, permissions, and re-analysis conditions for upgrade impact workflows
Design Goal: Predictable operation, safe transitions, transparent status

1) Core Concept — Analysis Lifecycle

Every analysis is a stateful object.

It moves through a defined sequence:

DRAFT
   ↓
INTAKE_VALIDATED
   ↓
ANALYSIS_RUNNING
   ↓
ANALYSIS_COMPLETE
   ↓
REVIEW_REQUIRED
   ↓
READY
   ↓
ARCHIVED

Additional interrupt states:

BLOCKED
FAILED
STALE
REQUIRES_REFRESH

No hidden transitions.
No silent updates.

2) State Definitions
DRAFT

Meaning:

Intake started but not submitted.

Typical cause:

user begins intake
required fields incomplete

Allowed actions:

Edit intake
Save draft
Delete draft
Submit intake

Not allowed:

Run analysis
Export report
INTAKE_VALIDATED

Meaning:

Required fields complete and structurally valid.

This is the system checkpoint before computation begins.

Allowed actions:

Start analysis
Edit intake
Cancel analysis
ANALYSIS_RUNNING

Meaning:

System actively processing KB and customer state comparison.

System behavior:

Lock intake fields
Show progress indicator
Prevent duplicate runs

Allowed actions:

View progress
Cancel run
ANALYSIS_COMPLETE

Meaning:

Processing finished successfully.
Results available.

Allowed actions:

View results
Export report
Assign review tasks

Transition logic:

If review items exist → REVIEW_REQUIRED
Else → READY
REVIEW_REQUIRED

Meaning:

Manual technical or functional review needed.

Typical triggers:

Customization detected
Integration surface matched
Schema change identified
Missing critical inputs

Allowed actions:

Assign reviewer
Add comments
Resolve review item
Mark review complete

Exit condition:

All review items resolved
READY

Meaning:

Analysis complete and no unresolved blocking items remain.

This is the operational signoff state.

Allowed actions:

Export report
Share report
Archive analysis
Initiate upgrade planning
ARCHIVED

Meaning:

Analysis closed and retained for recordkeeping.

System behavior:

Read-only
Immutable
Searchable
3) Interrupt States

These states can occur at any time.

BLOCKED

Meaning:

Required data missing.
Analysis cannot proceed safely.

Examples:

Missing target version
Missing KB coverage
Invalid intake structure

Allowed actions:

Fix intake
Re-validate
Restart analysis
FAILED

Meaning:

System error occurred during processing.

Examples:

KB ingestion failure
Data parsing failure
System exception

Allowed actions:

Retry analysis
View error details
Contact admin
STALE

Meaning:

Analysis results are outdated relative to source data.

Triggers:

New KB published
Customer state changed
Target version changed

Allowed actions:

Refresh analysis
Review changes
Archive old analysis
REQUIRES_REFRESH

Meaning:

System detected delta but refresh not yet executed.

Typical triggers:

New KB detected
Customer baseline updated
Configuration changed

Allowed actions:

Run refresh
View delta summary
Defer refresh
4) State Transition Diagram
DRAFT
  ↓
INTAKE_VALIDATED
  ↓
ANALYSIS_RUNNING
  ↓
ANALYSIS_COMPLETE
      ↓
   REVIEW_REQUIRED
      ↓
      READY
      ↓
     ARCHIVED

Interrupt paths:

ANY STATE → BLOCKED
ANY STATE → FAILED
READY → STALE
STALE → REQUIRES_REFRESH
REQUIRES_REFRESH → ANALYSIS_RUNNING
5) Trigger Events

These events cause state transitions.

User Triggers
Submit intake
Start analysis
Assign reviewer
Resolve review item
Export report
Archive analysis
System Triggers
New KB detected
Customer state updated
Validation failure detected
Processing error
Delta detected
Refresh completed
6) Permissions Model

We define role-based control here.

Roles
Viewer
Analyst
Reviewer
Admin
Viewer

Can:

View reports
View findings
Export reports

Cannot:

Edit intake
Run analysis
Approve review
Archive analysis
Analyst

Can:

Create intake
Run analysis
Edit intake
View results
Export reports

Cannot:

Approve final readiness
Modify system configuration
Reviewer

Can:

Review findings
Assign owners
Mark items resolved
Add comments

Cannot:

Modify intake
Run system refresh
Change KB catalog
Admin

Can:

Manage KB ingestion
Run delta refresh
Override states
Access audit logs
Modify configuration
7) Delta Refresh Model

This is critical for long-term reliability.

Sources of Change
Vendor KB updates
Customer configuration updates
Target version changes
Module enablement changes
Integration updates
Refresh Detection Logic
IF new source data detected

THEN

Mark analysis as STALE
Refresh Flow
Detect delta
   ↓
Mark analysis STALE
   ↓
Notify user
   ↓
Run refresh
   ↓
Recompute results
   ↓
Update report
8) Notification Rules

System notifications must be predictable.

Notify When
Analysis completed
Review required
Analysis blocked
New KB detected
Results stale
Refresh completed
Notification Channels
In-app notification
Email notification
Optional Slack / Teams integration
9) Audit Trail Requirements

Every transition must be logged.

Required fields:

state_transition:

  analysis_id
  previous_state
  new_state
  trigger_event
  user_id
  timestamp

This enables:

replayability
compliance
debugging
trust
10) Example Lifecycle

Realistic scenario:

User starts intake
→ DRAFT

User completes intake
→ INTAKE_VALIDATED

User runs analysis
→ ANALYSIS_RUNNING

Processing finishes
→ ANALYSIS_COMPLETE

System detects integration match
→ REVIEW_REQUIRED

Reviewer resolves items
→ READY

User exports report
→ ARCHIVED

New vendor update published
→ STALE
11) UI Integration Points

Each state should map directly to visible UI signals.

Status Badge Colors
READY — Green
REVIEW_REQUIRED — Orange
BLOCKED — Red
ANALYSIS_RUNNING — Blue
STALE — Yellow
ARCHIVED — Gray
12) MVP Workflow Scope

For initial release, support:

DRAFT
INTAKE_VALIDATED
ANALYSIS_RUNNING
ANALYSIS_COMPLETE
REVIEW_REQUIRED
READY
BLOCKED
STALE

Defer:

FAILED automation recovery
Advanced refresh scheduling
Multi-environment dependency orchestration