Phase 2 Build Plan v1

System: Upgrade Impact Analysis Tool
Purpose: Transform the Phase 1 working product path into a user-trustworthy MVP experience
Goal: Make the analysis results understandable, navigable, and actionable without redesigning core logic

1. Phase 2 Objectives

By the end of Phase 2, the system should support a polished user-facing path:

Open dashboard
→ understand current analysis state quickly
→ open results overview
→ see top risks, top actions, missing inputs, assumptions
→ drill into an application
→ filter/sort findings
→ open finding detail
→ understand what changed, why it matters, and what to do next

This phase is about:

comprehension speed
trust
adoption
decision support

Not adding new core analysis logic unless UX clarity depends on it.

2. Exit Criteria

Phase 2 is complete when all of the following are true:

Dashboard shows real analysis cards and useful summary metrics
Results Overview is readable in under one minute
Top risks and top actions are visible and prioritized
Application Detail supports filter/search and clear finding scanning
Finding Detail presents business and technical information cleanly
Blocked and unknown items are understandable without explanation from a developer
Primary user flow feels coherent and low-friction
UI uses real data only, not decorative placeholders

If users still need someone standing next to them saying “what it really means,” then Phase 2 is not done.

3. Phase 2 Scope

This phase includes six work packages:

WP-01 Dashboard Experience
WP-02 Results Overview Refinement
WP-03 Application Detail Usability
WP-04 Finding Detail Trust Layer
WP-05 Search / Filter / Prioritization
WP-06 UX States, Copy, and Interaction Hardening
WP-01 — Dashboard Experience
Goal

Turn the dashboard into a true landing page rather than a list with mild ambitions.

Required Behavior

Dashboard must answer, immediately:

what analyses exist
which one matters most
where risk is concentrated
what the next action should be
Required Components
A. Summary header
customer
environment
latest analysis date
overall status
B. status cards
Applies
Requires Review
Unknown
Blocked
C. latest analyses list
run / analysis ID
customer
environment
analysis date
overall status
applications count
D. top risks panel
E. top actions panel
Deliverables
Backend
dashboard aggregation endpoint refinement
sorting for newest/relevant analyses
top risks query
top actions query
Frontend
dashboard card layout
analysis list component
top risks component
top actions component
quick navigation into latest analysis
Testing
dashboard renders real counts
top risks show meaningful items
top actions show meaningful items
empty dashboard state is clear
WP-02 — Results Overview Refinement
Goal

Make the report overview the strongest “I trust this” screen in the system.

Required Behavior

Overview must present:

summary
assumptions
missing inputs
derived risks
application list

in a way that is obvious, not archaeological.

Required Components
A. summary banner
customer
environment
current/target versions
analysis date
overall status
B. executive summary cards
Applies
Requires Review
Unknown
Blocked
C. assumptions section
D. missing inputs section
E. derived risks section
F. application list
Required UX Improvements
prioritize blocked and unknown visually
collapse low-signal secondary content
make application drilldown obvious
ensure assumptions do not look like footnotes
Deliverables
Backend
derive and sort top risks
derive and sort top recommended actions
add lightweight application summary metrics
Frontend
overview page polish
risk/action prioritization blocks
assumptions/missing inputs layout
application summary table/card list
Testing
overview understandable from a fresh user session
blocked and unknown items visible above the fold
application drilldown obvious and working
WP-03 — Application Detail Usability
Goal

Make application-level review usable as a daily working screen.

Required Behavior

A user should be able to answer:

what findings affect this application
which findings are most severe
which findings require review
which ones are blocked/unknown
what action needs to happen next
Required Components
A. application header
application
current version
target version
status
B. finding list

Columns or cards:

Status
Severity
Change Type
Headline
Recommended Action
Source KB
C. filter/search panel
status
severity
taxonomy
review required
search text
Deliverables
Backend
application detail query supports filter params
sorting by severity/status
search on headline / KB number / taxonomy
Frontend
filter controls
search box
sortable finding list
status/severity badges
no-results state
minimal visual grouping by priority
Testing
filtering works
search works
findings sort predictably
no-results state is understandable
WP-04 — Finding Detail Trust Layer
Goal

Make the finding detail page strong enough that users stop arguing with the system and start arguing with reality instead.

Required Behavior

Finding detail must clearly show:

what changed
why it matters
what to do
what source proves it
what assumptions/gaps affect the conclusion
Required Components
A. finding header
headline
status
severity
taxonomy
application/module
version range
B. explanation block
What Changed
Why It Matters
Business Impact
Technical Impact
Recommended Action
C. source evidence block
KB article number
KB title
KB link
publication date
evidence excerpt
D. transparency block
assumptions
missing inputs
reason for status
E. expandable technical block
affected objects
affected features
affected integrations
Deliverables
Backend
ensure finding detail endpoint always returns complete source block
ensure reason_for_status is user-readable
ensure assumptions and missing inputs are finding-specific where possible
Frontend
finding detail layout polish
evidence callout card
expandable technical detail
copy-to-clipboard KB reference action
source link action
Testing
every finding detail has KB provenance
evidence excerpt visible
assumptions visible
blocked/unknown reasons readable

This is a hard requirement because the product promise depends on visible provenance and explainable results, not black-box conclusions.

WP-05 — Search / Filter / Prioritization
Goal

Reduce cognitive load and help users find the important things quickly.

Required Behavior

Users must be able to:

search by application
search by KB article number
filter by status
filter by severity
filter by taxonomy
filter by review required
see highest-priority findings first
Prioritization Rules v1

Default finding order should prefer:

BLOCKED
REQUIRES_REVIEW
UNKNOWN
APPLIES
DOES_NOT_APPLY

Within those, sort by:

severity
application
headline
Deliverables
Backend
search endpoint refinement
server-side filtering where appropriate
priority ranking helper for findings display
Frontend
unified filter bar
removable active filter chips
“clear filters” control
default high-priority sort
Testing
search by KB works
search by headline works
default ordering emphasizes actionable items
filter chips reflect actual state
WP-06 — UX States, Copy, and Interaction Hardening
Goal

Make the system feel finished enough to be trusted even before every advanced feature exists.

Required States to Harden
Loading states

Must be calm and obvious.

Empty states

Must explain what happened and what to do next.

Error states

Must be user-readable, not stack-shaped.

Blocked states

Must explain which required inputs are missing.

Unknown states

Must explain which conclusions could not be determined.

Required Copy Improvements

We should standardize copy for:

blocked analysis
unknown finding
missing integration inventory
missing customization inventory
no KB coverage
no applicable findings
Deliverables
Frontend
reusable empty state component
reusable error state component
reusable blocked/unknown explanatory banner
standardized status badge labels
Backend
ensure error envelope is user-translatable
ensure missing data responses are field-specific
Testing
blocked experience readable
unknown experience readable
empty states guide next action
error states do not require interpretation by an engineer
4. Recommended Build Order

Safest sequence:

WP-04 Finding Detail Trust Layer
WP-02 Results Overview Refinement
WP-03 Application Detail Usability
WP-01 Dashboard Experience
WP-05 Search / Filter / Prioritization
WP-06 UX States, Copy, and Interaction Hardening

Reason:

trust object first
overview second
working screen third
landing page fourth
convenience and polish after comprehension
5. Concrete Task List
Backend Tasks
Refine dashboard aggregation queries
Add top risks/top actions derivation
Refine results overview response shape
Add application-level summary metrics
Add application filtering/sorting query support
Add search support for findings
Add finding priority ordering helper
Refine finding detail response with full evidence block
Refine reason_for_status for user readability
Ensure field-level missing input messages are explicit
Frontend Tasks
Polish dashboard layout
Build top risks and top actions panels
Polish results overview layout
Build assumptions and missing inputs blocks
Build derived risks panel
Build application finding filter bar
Build search input for findings
Add status/severity badge system
Polish finding detail layout
Add evidence citation card
Add transparency section
Add expandable technical section
Implement reusable empty/loading/error components
Implement blocked/unknown state banners
Product/UX Tasks
Standardize user-facing status labels
Standardize blocked/unknown copy
Standardize assumptions copy style
Define default severity color semantics
Define default finding sort order
Review screens for one-minute comprehension
6. Minimum Testing Scope
Backend
dashboard metrics correct
top risks/top actions deterministic
application filters deterministic
finding search deterministic
finding detail always source-backed
Frontend
dashboard renders real data
overview is readable
filtering/search works
finding detail clearly exposes evidence
blocked/unknown states are understandable
empty and error states are actionable
User-path tests
open dashboard
open latest analysis
inspect top risks
drill into application
filter findings
open finding detail
identify source KB without confusion
7. What Not to Build in Phase 2

Do not build yet:

review item assignment workflow
comments
exports beyond simple placeholder
admin trace viewer
delta refresh orchestration
notification system
full Oracle KB parser automation

Why:

Because Phase 2 is about making the current truth path usable, not broadening scope until the UX collapses under the weight of ambition and committee vitamins.

8. Recommended Demo at End of Phase 2

You should be able to show:

Dashboard with latest analysis and clear status
Results Overview with:
counts
assumptions
missing inputs
top risks
top actions
Application Detail with filterable findings
Finding Detail with:
plain-language impact
technical impact
recommended action
Oracle KB number
title
link
evidence excerpt
Blocked / unknown state examples that are understandable

That is the first version that people can credibly say they would use.

9. Risks in Phase 2
Risk 1

UI polish becomes a substitute for clarity.

Mitigation:

optimize for comprehension, not gloss
Risk 2

Top risks and top actions become hand-wavy.

Mitigation:

derive them deterministically from findings and statuses
Risk 3

Filters/search expose weak data shape.

Mitigation:

refine response shape before piling on controls
Risk 4

Technical details bleed into business view by default.

Mitigation:

progressive disclosure only
10. Definition of Done

Phase 2 is done when:

dashboard is useful
overview is readable
application detail is workable
finding detail is trustworthy
blocked and unknown states are explainable
users can find high-priority issues quickly
the product feels coherent, not just correct