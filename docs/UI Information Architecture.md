UI Information Architecture v1

System: Upgrade Impact Analysis Tool
Purpose: Define the user-facing screen structure, navigation model, and information hierarchy for a high-trust upgrade analysis experience
Design Goal: Easy to use, easy to understand, hard to misuse

1. UX Design Principles

The UI must optimize for two things:

acceptance
accuracy comprehension

That means the interface must:

explain results in plain language
show evidence for every important claim
separate summary from technical detail
surface missing inputs clearly
avoid forcing users into admin concepts unless necessary

This should not feel like a parser console wearing a tie.

2. Primary User Types

We should explicitly design for at least four user types.

A. Business Stakeholder

Needs to know:

what changed
what matters
where risk exists
what action is needed

Does not need:

parser status
content hashes
ingestion traces
B. Functional Analyst / Delivery Lead

Needs to know:

which findings apply
which modules are affected
which items require review
which missing inputs are blocking accuracy
C. Technical Reviewer / Developer

Needs to know:

affected objects
integrations impacted
evidence excerpts
exact KB references
why an item is flagged as review-required
D. Admin / Operator

Needs to know:

ingestion status
KB normalization status
delta refresh status
schema validation failures
trace IDs / batch IDs / audit records

This user belongs in a separate layer by default.

3. Navigation Model

The system should have two layers:

Primary Layer — User Experience

For normal users.

Secondary Layer — Admin / Operations

For support, maintenance, and audit users.

That separation should be structural, not cosmetic.

4. Primary Layer Screen Map

The primary UX should have these screens:

1. Home / Dashboard
2. Analysis Intake
3. Analysis Results Overview
4. Application Detail
5. Finding Detail
6. Review Queue
7. Export / Share
5. Secondary Layer Screen Map

The admin layer should have these screens:

1. KB Catalog Admin
2. Customer State Admin
3. Delta Refresh Monitor
4. Normalization Review
5. Audit / Trace Viewer
6. System Health / Validation
PRIMARY LAYER
6. Screen 1 — Home / Dashboard
Purpose

Give the user immediate situational awareness.

Must show
analyses available
current customer / environment
latest run date
overall status
number of applications in scope
count of findings by status
count of blocked / unknown items
Recommended layout

Top row:

Customer
Environment
Analysis Date
Overall Status

Second row:

Applicable Findings
Requires Review
Unknown
Blocked

Third row:

Top Risks
Top Actions
User actions
start new analysis
open latest analysis
filter by environment
open review queue
UX note

This should feel like a clean control panel, not an admin log viewer.

7. Screen 2 — Analysis Intake
Purpose

Collect required customer input in a structured way.

Must show
required intake fields
optional enhancement fields
upload options
completeness indicator
validation messages
Sections
customer info
environment info
applications in scope
current versions
target versions
modules enabled
customizations
integrations
reports / jobs
KB source references if user-supplied
User actions
add application
upload intake file
edit section
save draft
validate intake
submit for analysis
UX note

This screen is critical for acceptance. It must feel guided, not punitive.

Recommended interaction
progressive sections
inline help text
“why we ask this” hints
clearly labeled required vs optional fields
8. Screen 3 — Analysis Results Overview
Purpose

Present the top-level report in a way users can understand in under a minute.

Must show
summary banner
executive summary metrics
assumptions
missing inputs
derived risks
applications in scope
quick links to drilldown
Sections
A. Summary Banner
Customer
Environment
Current / Target versions
Analysis date
Overall status
B. Executive Summary Cards
Applies
Requires Review
Unknown
Blocked
C. Top Risks
D. Top Recommended Actions
E. Assumptions
F. Missing Inputs
G. Application List
User actions
drill into application
filter findings
toggle business / technical view
export report
UX note

This is the “trust me or don’t” screen. It has to be calm, obvious, and readable.

9. Screen 4 — Application Detail
Purpose

Show all findings for one application.

Must show
application name
current version
target version
application status
application summary
finding list
application-specific missing inputs
application-specific risks
Finding list columns
Status
Severity
Change Type
Headline
Recommended Action
Source KB
Filters
status
severity
taxonomy
functional area
review required
missing data impact
User actions
open finding detail
filter findings
switch business / technical mode
export application report
UX note

This screen should behave like a decision workspace, not a spreadsheet.

10. Screen 5 — Finding Detail
Purpose

Provide the full detail for one finding.

This is the core trust object in the whole app.

Must show
Top section
Headline
Status
Severity
Change Taxonomy
Application / Module
Applies to version range
Main explanation
What changed
Why it matters
Business impact
Technical impact
Recommended action
Evidence section
KB article number
KB title
source link
publication date
evidence excerpt
reference section if available
Transparency section
assumptions used
missing inputs affecting this finding
why this was marked applies / review / unknown
Expandable technical panel
affected objects
affected features
affected integrations
comparison notes
review flags
User actions
mark for review
assign owner
add comment
copy KB reference
open source link
UX note

This is where the user either trusts the system or starts calling it a liar. The KB citation must be impossible to miss.

11. Screen 6 — Review Queue
Purpose

Turn analysis into work.

Must show
findings requiring technical review
blocked items
unknown items
assigned owners
recommended next actions
Queue columns
Application
Finding
Reason for Review
Status
Owner
Due Date
Source KB
Filters
owner
app
review type
blocked vs unknown vs review-required
User actions
assign owner
mark in progress
mark resolved
export queue
UX note

This is the bridge from “interesting report” to “real operational use.”

12. Screen 7 — Export / Share
Purpose

Let users generate outputs without changing the truth.

Export options
full report PDF
application-only PDF
review queue CSV / Excel
technical appendix
admin JSON artifact, if permitted
Must show
export scope
generated date
report version
traceability footer
UX note

Exports should preserve the same evidence and assumptions visible in-app.

SECONDARY LAYER
13. Admin Screen 1 — KB Catalog Admin
Purpose

Manage Oracle KB ingestion and normalization.

Must show
KB articles loaded
normalization status
source versions covered
duplicate / changed KB detection
delta refresh readiness
User actions
ingest KB batch
reprocess failed articles
inspect normalized change records
mark for review
14. Admin Screen 2 — Customer State Admin
Purpose

Manage current-state baselines and delta updates.

Must show
customer snapshots
latest update date
completeness score
changed fields since prior baseline
User actions
upload new baseline
compare baselines
approve delta update
flag incomplete submissions
15. Admin Screen 3 — Delta Refresh Monitor
Purpose

Track periodic updates.

Must show
KB deltas detected
customer-state deltas detected
analyses needing rerun
failed refreshes
User actions
run refresh
rerun analysis
acknowledge update
inspect changed artifacts
16. Admin Screen 4 — Normalization Review
Purpose

Handle edge cases in KB parsing.

Must show
extracted records needing review
partial extractions
failed normalization
source evidence side-by-side
User actions
approve normalized record
reject / flag
edit mapping rules if allowed
send to governance review

This should not leak into primary UX.

17. Admin Screen 5 — Audit / Trace Viewer
Purpose

Provide deep traceability.

Must show
analysis run ID
ingestion run IDs
source snapshot IDs
schema versions
content hashes
decision trace
User actions
open raw artifact
inspect provenance
export audit trail

This is where hard questions go to die honorably.

18. Admin Screen 6 — System Health / Validation
Purpose

Monitor system quality.

Must show
schema validation failures
missing KB mappings
stale customer baselines
incomplete analyses
refresh failures
User actions
rerun validations
inspect failed records
export system health summary
CROSS-CUTTING UX RULES
19. Business View vs Technical View

This should be a system-wide toggle in the primary layer.

Business View

Shows:

plain-language summaries
business impact
severity
recommended actions
source KB
Technical View

Adds:

affected objects
integration surfaces
version applicability
evidence excerpts
review flags

Same truth. Different presentation.

20. Evidence Visibility Rule

Every important finding must show:

KB article number
KB title
KB link

No exceptions.

If a finding cannot cite a KB, it does not belong in the primary UX.

This supports the trust-first design that the current system architecture depends on.

21. Missing Data Visibility Rule

Missing data must never be hidden.

It should appear:

at report overview
at application level
at finding level if relevant

Users should never mistake “unknown” for “safe.”

22. Progressive Disclosure Rule

Default user experience:

simple
readable
decision-oriented

Advanced detail:

available
expandable
never forced

That matches the established UI approach for MK1: keep the main flow obvious, expose deeper diagnostics where useful, and avoid dense dashboards as the default.

23. Search and Filter Requirements

Primary layer must support:

search by application
search by KB article number
filter by status
filter by severity
filter by taxonomy
filter by review-required
filter by missing input impact

If users cannot find what matters quickly, they will go back to spreadsheets like it’s 2009 and somehow worse.

24. Empty State Requirements

The UI must handle:

no analyses yet
incomplete intake
blocked analysis
no applicable findings
no KB coverage for application

Each empty state must explain:

what happened
why
what the user should do next
25. Mobile / Responsive Principle

This is probably desktop-first, but the primary screens should remain readable on smaller viewports.

Priority order for responsiveness:

Overview
Application Detail
Finding Detail

Admin screens can be less elegant without causing a small civil war.

26. Recommended MVP Screen Order

For first implementation, I would prioritize:

Phase 1
Home / Dashboard
Analysis Intake
Results Overview
Application Detail
Finding Detail
Phase 2
Review Queue
Export / Share
Phase 3
Admin screens
deeper trace viewer
normalization review tools

This sequencing preserves acceptance-first delivery.