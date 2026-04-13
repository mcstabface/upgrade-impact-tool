Phase 1 Build Plan v1

System: Upgrade Impact Analysis Tool
Purpose: Deliver the first real end-to-end user workflow from intake through evidence-backed analysis results
Goal: Produce a trustworthy MVP slice without redesigning foundation

1. Phase 1 Objectives

By the end of Phase 1, the system should support a real working flow:

Create intake
→ validate intake
→ persist customer snapshot
→ run analysis
→ match customer context against normalized change records
→ generate findings
→ render results overview
→ drill into application detail
→ drill into finding detail with KB evidence

This is the first slice that users can actually judge.

2. Exit Criteria

Phase 1 is complete when all of the following are true:

Validated intake creates immutable customer snapshot
Analysis run executes against real seeded/ingested change records
Deterministic applicability logic produces findings
Results overview shows real counts and real findings
Application detail lists real findings
Finding detail shows KB provenance and evidence excerpt
Blocked and unknown cases render correctly
Assumptions and missing inputs are visible in results

If those are not true, then Phase 1 is still just a dressed-up stub.

3. Phase 1 Scope

This phase includes five real functional slices:

WP-01 Intake Validation Engine
WP-02 Customer Snapshot Persistence
WP-03 KB / Change Record Baseline Ingestion
WP-04 Deterministic Applicability Engine
WP-05 Results Retrieval and UI Binding
WP-01 — Intake Validation Engine
Goal

Replace placeholder validation with actual deterministic rules.

Required Behavior

Validation must:

block missing required fields
warn on missing optional-but-important fields
compute completeness score
return explicit missing field list
return explicit warning list
Required Rules
Hard-blocking required fields
customer_name
environment_name
environment_type
at least one application
application_name
current_version
target_version
modules_enabled
Warning-only fields
customizations
integrations
jobs/reports
business contact
technical contact
Deliverables
Backend
validation rules module
intake validation service
deterministic completeness scoring
structured validation response
Frontend
inline validation messaging
blocked submission state
warning display
completeness progress indicator
Output Example
{
  "status": "INTAKE_VALIDATED",
  "completeness_score": 78,
  "missing_required_fields": [],
  "warnings": [
    "No integration inventory provided for Payroll",
    "No customization inventory provided for Accounts Payable"
  ]
}
Testing
missing target version blocks
empty modules list blocks
no integrations warns
same input returns same score/result
WP-02 — Customer Snapshot Persistence
Goal

Persist validated intake as immutable customer truth for analysis.

Required Behavior

When intake is validated and analysis starts:

create a new customer_state_snapshot
create related application/module records
compute content_hash
mark snapshot active if current
preserve prior snapshots unchanged

This follows the immutable-artifact model directly: new state becomes a new record rather than mutating prior truth.

Deliverables
Backend
intake-to-snapshot mapper
snapshot persistence service
content hash generation
active snapshot selection logic
UI/API
intake detail returns persisted snapshot linkage
analysis creation returns snapshot ID used
Testing
validated intake creates snapshot
same content hash is stable for same input
updated intake creates new snapshot, not overwrite
active snapshot switches correctly
WP-03 — KB / Change Record Baseline Ingestion
Goal

Move from pure seed fiction to the first real baseline change catalog.

Phase 1 Constraint

Do not build the full Oracle KB parser yet.
Instead, implement the smallest controlled ingestion baseline:

seed-backed or manually curated Oracle KB records
manually curated normalized change records
evidence excerpts attached
version coverage for 2–3 applications

This is the right compromise: real enough to validate system behavior, small enough to stay controlled.

Required Data Coverage

Minimum:

Applications:
- Accounts Payable
- Payroll

Change examples:
- one behavioral
- one workflow
- one integration
- one blocked/unknown case via missing data
- one review-required case via customization/integration flag
Deliverables
Backend
KB article ingestion loader
KB version loader
change record loader
evidence loader
provenance enforcement rule
Rule

No change record may be active without:

KB article number
KB title
KB link

That is mandatory because visible trust depends on source-backed findings.

Testing
KB records load cleanly
change records reference valid KBs
evidence exists for displayed findings
invalid KB-less record is rejected
WP-04 — Deterministic Applicability Engine
Goal

Produce real findings from customer state + normalized change records.

This is the core logic slice for Phase 1.

Required Matching Logic v1

For a change record to be considered for a customer application:

Rule 1 — Application match
change.application_name == customer.application_name
Rule 2 — Version relevance
change.version_from <= target_version
AND
change.version_to >= current_version

Or equivalent normalized version-window logic.

Rule 3 — Module relevance

If change has module name:

change.module_name in customer.modules_enabled
Rule 4 — Review-required escalation

If either of these is true:

customization_review_required = true and customer customizations exist or are unknown
integration_review_required = true and customer integrations exist or are unknown

Then:

finding_status = REQUIRES_REVIEW
Rule 5 — Unknown

If applicability cannot be determined due to missing input:

finding_status = UNKNOWN
Rule 6 — Blocked

If required source coverage is missing:

finding_status = BLOCKED
Phase 1 Output Model

Generate:

analysis_run
analysis_applications
analysis_findings
finding_evidence
state_transitions
Deliverables
Backend
applicability engine service
findings generation service
counts aggregation service
assumptions builder
missing inputs builder
derived risks builder
Important Constraint

No LLM logic here.
This phase should be entirely deterministic and auditable.

Testing
application/version/module match produces APPLIES
missing customization data produces UNKNOWN or REQUIRES_REVIEW where appropriate
missing KB coverage produces BLOCKED
rerun with same inputs produces same findings
WP-05 — Results Retrieval and UI Binding
Goal

Replace seeded static result views with live analysis data.

Required Screens to Activate
1. Results Overview

Must show:

summary counts
assumptions
missing inputs
derived risks
application list
2. Application Detail

Must show:

application-level status
finding list
filters
recommended actions
KB references
3. Finding Detail

Must show:

headline
status
severity
change taxonomy
plain-language summary
business impact
technical impact
recommended action
KB article number
KB title
KB link
evidence excerpt
assumptions
missing inputs
reason for status
Deliverables
Backend
populate overview endpoint from real findings
populate application detail endpoint from real findings
populate finding detail endpoint from real evidence
Frontend
replace stubbed data fetches
bind screens to live responses
handle loading / empty / error / blocked states
add business vs technical progressive disclosure
Testing
results overview displays real counts
application detail displays correct findings
finding detail always shows KB citation
unknown/blocked states render legibly
4. Recommended Build Order

Safest sequence:

WP-01 Intake Validation Engine
WP-02 Customer Snapshot Persistence
WP-03 KB / Change Record Baseline Ingestion
WP-04 Deterministic Applicability Engine
WP-05 Results Retrieval and UI Binding

Reason:

validate input first
persist truth second
ensure source catalog exists
run comparison
then bind UI to actual truth
5. Concrete Task List
Backend Tasks
Implement validation rule engine
Implement completeness score calculator
Implement intake-to-snapshot mapper
Implement snapshot persistence service
Implement content hash generator
Create KB baseline loader
Create change record loader
Implement provenance validation
Implement version comparison utility
Implement application/module matching logic
Implement findings generation service
Implement assumptions builder
Implement missing inputs builder
Implement derived risks builder
Implement overview aggregation queries
Implement application detail query
Implement finding detail query
Frontend Tasks
Connect intake validation screen to live validator
Render completeness score and warnings
Bind results overview to live analysis endpoint
Bind application detail to live endpoint
Bind finding detail to live endpoint
Render assumptions section
Render missing inputs section
Render derived risks section
Render evidence citation block
Handle blocked and unknown states cleanly
Docs Tasks
Document validation rules v1
Document applicability logic v1
Document version comparison assumptions
Document sample KB baseline coverage
Document known Phase 1 limitations
6. Minimum Testing Scope
Backend
validation rules deterministic
snapshot creation immutable
KB provenance required
applicability engine produces correct statuses
findings persist correctly
overview counts equal aggregated finding statuses
Frontend
intake validation messages visible
overview counts and sections render
application drilldown works
finding detail shows source citation and evidence
blocked state visible
unknown state visible
End-to-End
create intake
validate intake
start analysis
open results overview
open application detail
open finding detail

If that path fails, Phase 1 failed.

7. What Not to Build in Phase 1

Do not build yet:

review queue
comments/assignment workflow
refresh/delta orchestration
admin trace viewer
notification system
full Oracle KB parser automation
exports beyond minimal placeholder

Reason:
Phase 1 is about proving the product truth path, not building every annex to the building.

8. Recommended Demo at End of Phase 1

You should be able to show:

User creates intake
System blocks missing required data
User fixes intake
System validates and starts analysis
Results Overview shows:
counts
assumptions
missing inputs
derived risks
User opens Accounts Payable
User opens “Invoice validation behavior updated”
System shows:
status
impact
action
Oracle KB number
KB title
source link
evidence excerpt

That is enough to make the system feel real.

9. Risks in Phase 1
Risk 1

Version comparison logic becomes ambiguous.

Mitigation:

define explicit version normalization rules
document supported version formats for v1
Risk 2

Baseline KB data is too thin to test UX meaningfully.

Mitigation:

include multiple statuses and multiple applications
Risk 3

UI tries to render admin complexity in primary views.

Mitigation:

keep business/technical disclosure disciplined
no ingestion metadata in core user flow
Risk 4

Unknown vs blocked semantics get muddled.

Mitigation:

enforce status rules in applicability engine tests
10. Definition of Done

Phase 1 is done when:

real validated intake produces immutable snapshot
real analysis produces persisted findings
findings have KB provenance
results overview is live
application detail is live
finding detail is live
assumptions, missing inputs, and evidence are visible
repeated run with same input is deterministic