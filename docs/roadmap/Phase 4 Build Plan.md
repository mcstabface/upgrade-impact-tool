Phase 4 Build Plan v1

System: Upgrade Impact Analysis Tool
Purpose: Introduce controlled refresh, delta detection, and administrative visibility
Goal: Keep analyses current without corrupting history

1. Phase 4 Objectives

By the end of Phase 4, the system should support this lifecycle:

New KB published
or
Customer configuration changes

→ system detects change
→ existing analysis marked STALE
→ user triggers refresh
→ new analysis run created
→ delta summary generated
→ prior analysis preserved

This phase ensures the system can operate continuously, not just once.

2. Exit Criteria

Phase 4 is complete when:

System detects changes in KB catalog
System detects changes in customer snapshot
Analysis can be marked STALE deterministically
Refresh creates new analysis run
Prior analysis remains unchanged
Delta summary shows what changed
Admins can inspect KB and snapshot state
Audit trail shows refresh lineage
3. Phase 4 Scope

Six work packages:

WP-01 Change Detection Engine
WP-02 Staleness Evaluation
WP-03 Controlled Refresh Execution
WP-04 Delta Summary Generation
WP-05 Administrative Inspection Views
WP-06 Audit and Lineage Tracking
WP-01 — Change Detection Engine
Goal

Detect whether relevant source data has changed since the last analysis.

Required Behavior

System must compare:

KB catalog state
Customer snapshot state
Analysis input state

against the last analysis.

Detection Triggers
KB change triggers
New KB article added
Existing KB article updated
Change record version updated
Customer change triggers
New application added
Application version changed
Module configuration changed
Integration list changed
Customization list changed
Detection Method

Use deterministic fingerprints.

content_hash
version_hash
snapshot_hash
Deliverables
Backend

Implement:

kb_change_detector
snapshot_change_detector
analysis_input_hash comparator
Testing
New KB triggers change detection
Updated snapshot triggers change detection
No change produces no detection
Same data produces same hash
WP-02 — Staleness Evaluation
Goal

Determine whether an analysis is still valid.

Required Behavior

Analysis status must transition to:

STALE

when relevant changes are detected.

Staleness Rules

An analysis becomes stale if:

New relevant KB exists
Customer snapshot changed
Missing input resolved
Configuration updated
Deliverables
Backend

Implement:

staleness evaluator
analysis status updater
Testing
New KB marks analysis stale
Snapshot change marks analysis stale
Unrelated KB does not mark stale
Repeated evaluation deterministic
WP-03 — Controlled Refresh Execution
Goal

Re-run analysis safely without overwriting history.

Required Behavior

Refresh must:

Create new analysis run
Reuse latest snapshot
Run applicability engine
Persist new findings
Link to prior analysis
Required Rule

Never overwrite previous analysis.

Instead:

analysis_run.previous_analysis_id

must be recorded.

Deliverables
Backend

Implement:

refresh service
analysis duplication logic
lineage link generator
Testing
Refresh creates new analysis
Previous analysis remains unchanged
New analysis references prior run
Multiple refresh cycles preserve lineage
WP-04 — Delta Summary Generation
Goal

Show users exactly what changed between runs.

Required Behavior

System must generate:

New findings
Updated findings
Resolved findings
Removed findings
New KB articles
Updated KB articles
Required Output
Delta Summary

must be human-readable.

Example
New KB articles: 2
Updated KB articles: 1

Applications impacted:
Accounts Payable
Payroll

New findings: 3
Resolved findings: 1
Updated findings: 2
Deliverables
Backend

Implement:

delta comparison engine
finding difference detector
summary builder
Testing
New finding detected correctly
Resolved finding detected correctly
Unchanged finding ignored
Summary deterministic
WP-05 — Administrative Inspection Views
Goal

Give administrators visibility into system state.

Required Views
KB Catalog Admin

Must display:

KB article count
KB ingestion status
Last ingestion time
Normalization failures
Customer Snapshot Admin

Must display:

Active snapshot
Snapshot history
Snapshot timestamp
Snapshot content hash
Analysis Admin

Must display:

Analysis history
Refresh lineage
Status transitions
Run timestamps
Deliverables
Frontend

Implement:

KB catalog admin screen
Snapshot admin screen
Analysis admin screen
Backend

Implement:

admin inspection endpoints
Testing
Admin views load correctly
History visible
Lineage visible
Hashes visible
WP-06 — Audit and Lineage Tracking
Goal

Provide traceability for every refresh and change.

Required Behavior

Every refresh must record:

timestamp
user
trigger
previous analysis
new analysis
changes detected
Required Storage
refresh_events
state_transitions
analysis_lineage
Deliverables
Backend

Implement:

refresh event logger
lineage tracker
audit query endpoint
Testing
Refresh event logged
Lineage chain intact
Audit query returns correct history
Multiple refresh cycles traceable
4. Recommended Build Order

Safest sequence:

1 Change Detection Engine
2 Staleness Evaluation
3 Controlled Refresh Execution
4 Delta Summary Generation
5 Audit and Lineage Tracking
6 Administrative Inspection Views

Reason:

Detect → mark stale → refresh → explain change → record history → expose visibility.

5. Concrete Task List
Backend Tasks
Implement KB hash generator
Implement snapshot hash generator
Implement change detection service
Implement staleness evaluator
Implement refresh execution service
Implement analysis lineage tracking
Implement delta comparison engine
Implement refresh event logging
Implement admin inspection endpoints
Frontend Tasks
Create refresh button
Create stale status indicator
Create delta summary panel
Create admin inspection screens
Display lineage history
Display refresh history
Documentation Tasks
Document staleness rules
Document refresh rules
Document delta calculation logic
Document lineage tracking rules
Document admin inspection behavior
6. Minimum Testing Scope
Backend
Change detection deterministic
Staleness detection deterministic
Refresh creates new analysis
Delta summary accurate
Lineage preserved
Audit history complete
Frontend
Stale indicator visible
Refresh action works
Delta summary readable
Admin inspection screens load
Lineage visible
End-to-End
Run analysis
Modify KB
System marks stale
Trigger refresh
New analysis created
Delta summary generated
History preserved
7. What Not to Build in Phase 4

Do not build:

Automatic refresh scheduling
Email alerts
Notification workflows
External integrations
Bulk refresh orchestration
Performance tuning
Multi-tenant scaling

Those belong later.

Right now we are building:

controlled refresh and visibility

8. Recommended Demo at End of Phase 4

You should be able to show:

Existing analysis visible
New KB added
Analysis marked STALE
User clicks Refresh
New analysis run created
Delta summary displayed
Prior analysis still accessible
Lineage history visible

That demonstration proves the system can operate safely over time.

9. Risks in Phase 4
Risk

Refresh overwrites history.

Mitigation:

Never update prior analysis records
Always create new analysis run
Risk

Staleness logic too sensitive.

Mitigation:

Define explicit relevance rules
Ignore unrelated changes
Risk

Delta summaries confusing.

Mitigation:

Use clear categories
Use plain-language summaries
Avoid raw diff output
10. Definition of Done

Phase 4 is done when:

System detects changes reliably
Analyses marked stale correctly
Refresh produces new run
Prior runs preserved
Delta summary explains change
Admin views expose system state
Audit history complete