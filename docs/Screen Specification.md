Screen Specification v1

System: Upgrade Impact Analysis Tool
Scope: Phase 1 — Core User Experience
Design Goal: Fast comprehension, high trust, low friction adoption

Screen 1 — Home / Dashboard
Purpose

Provide immediate situational awareness and entry point into the system.

This screen answers:

What analyses exist?
What is the current status?
Where should I focus first?

If this screen is confusing, adoption drops immediately.

Primary User Types
Business Stakeholder
Delivery Lead
Functional Analyst
Required Data Inputs
analysis_runs:

  - run_id
  - customer_name
  - environment_name
  - analysis_date
  - overall_status
  - applications_count
  - applies_count
  - review_required_count
  - unknown_count
  - blocked_count
Displayed Components
Component 1 — Header Banner

Fields:

Customer
Environment
Latest Analysis Date
Overall Status

Behavior:

Always visible
Updates dynamically when a different analysis is selected
Component 2 — Status Summary Cards

Cards displayed horizontally.

Applies
Requires Review
Unknown
Blocked

Example:

Applies: 14
Requires Review: 5
Unknown: 3
Blocked: 2
Component 3 — Analysis List

Table columns:

Run ID
Customer
Environment
Analysis Date
Overall Status
Applications
Component 4 — Top Risks Panel

Shows highest-priority derived risks.

Example:

Custom validation workflow may be impacted
Missing integration inventory for Payroll
No KB coverage for Reporting module
Component 5 — Top Actions Panel

Shows actionable next steps.

Example:

Provide integration inventory
Review Accounts Payable validation logic
Confirm reporting module documentation
User Actions
Open analysis
Start new analysis
Filter by environment
Search by customer
Validation Rules
No analyses exist:
Display empty state message
Empty State
No upgrade analyses found.

To begin:

Create a new analysis using the Intake workflow.
Screen 2 — Analysis Intake
Purpose

Collect structured customer state data required to run analysis.

This is the most operationally sensitive screen.

Bad UX here = incomplete data
Incomplete data = unreliable results
Unreliable results = tool rejection

Primary User Types
Delivery Lead
Functional Analyst
Customer Implementation Team
Required Data Inputs
customer:

  customer_name
  environment_name
  environment_type

applications:

  - application_name
  - current_version
  - target_version
  - modules_enabled
Displayed Components
Component 1 — Intake Progress Indicator

Example:

Customer Info — Complete
Applications — In Progress
Integrations — Not Started
Review — Not Started
Component 2 — Customer Information Form

Fields:

Customer Name
Environment Name
Environment Type
Primary Contact
Component 3 — Applications Section

Fields:

Application Name
Current Version
Target Version
Modules Enabled
Component 4 — Integrations Section (Optional)

Fields:

Integration Name
Source System
Target System
Interface Type
Schedule
Component 5 — Upload Intake File

Supports:

CSV
Excel
JSON
Component 6 — Completeness Indicator

Example:

Completeness Score: 78%
User Actions
Add application
Upload intake file
Save draft
Validate intake
Submit analysis
Validation Rules

Required fields:

Application Name
Current Version
Target Version
Modules Enabled

If missing:

Block submission
Error State
Submission blocked.

Missing required fields:

Target Version
Modules Enabled
Empty State
No applications defined.

Add an application to continue.
Screen 3 — Analysis Results Overview
Purpose

Present the high-level report in a way that can be understood in under 60 seconds.

This is the system’s trust checkpoint.

Primary User Types
Business Stakeholder
Delivery Lead
Technical Reviewer
Required Data Inputs
report_summary:

  customer_name
  environment_name
  analysis_date
  overall_status

  applies_count
  review_required_count
  unknown_count
  blocked_count

assumptions:

missing_inputs:

derived_risks:

applications:
Displayed Components
Component 1 — Summary Banner

Fields:

Customer
Environment
Current Version
Target Version
Analysis Date
Overall Status
Component 2 — Executive Summary Cards
Applies
Requires Review
Unknown
Blocked
Component 3 — Assumptions Section

Example:

Standard application usage assumed
Integration impact evaluated only for provided interfaces
Component 4 — Missing Inputs Section

Example:

No integration inventory provided
No customization inventory provided
Component 5 — Derived Risks Section

Example:

Integration impact may be understated
Custom workflow behavior may change
Component 6 — Application List

Columns:

Application
Current Version
Target Version
Status
Findings
User Actions
Open application detail
Filter by status
Toggle business / technical view
Export report
Validation Rules
Report must include KB references

If missing:

Display system error
Screen 4 — Application Detail
Purpose

Show all findings for one application.

This is the working screen for analysts.

Primary User Types
Delivery Lead
Functional Analyst
Technical Reviewer
Required Data Inputs
application:

  name
  current_version
  target_version
  findings:

    - finding_id
    - status
    - severity
    - change_taxonomy
    - headline
    - recommended_action
    - kb_reference
Displayed Components
Component 1 — Application Header
Application Name
Current Version
Target Version
Application Status
Component 2 — Finding Table

Columns:

Status
Severity
Change Type
Headline
Recommended Action
KB Reference
Component 3 — Filters Panel
Status
Severity
Taxonomy
Functional Area
Review Required
User Actions
Open finding detail
Filter findings
Search findings
Export application report
Empty State
No findings detected for this application.

Upgrade impact minimal based on current inputs.
Screen 5 — Finding Detail
Purpose

Provide complete detail and evidence for one finding.

This is the system’s credibility screen.

Primary User Types
Technical Reviewer
Delivery Lead
Auditor
Required Data Inputs
finding:

  headline
  status
  severity
  taxonomy
  application
  module
  version_range

  summary
  business_impact
  technical_impact
  recommended_action

  kb_reference:
    number
    title
    url
    publication_date

  evidence_excerpt

  assumptions
  missing_inputs
Displayed Components
Component 1 — Finding Header
Headline
Status
Severity
Change Type
Applies to Version Range
Component 2 — Explanation Section
What Changed
Why It Matters
Business Impact
Technical Impact
Recommended Action
Component 3 — Evidence Section
KB Article Number
KB Title
Source Link
Publication Date
Evidence Excerpt
Component 4 — Transparency Section
Assumptions Used
Missing Inputs
Reason for Status
User Actions
Assign owner
Add comment
Mark for review
Copy KB reference
Open source link
Validation Rules
KB reference required

If missing:

Block display
Empty State
Finding details unavailable.

Source evidence not found.
Phase 1 Implementation Priority

Build in this order:

1 — Analysis Intake
2 — Results Overview
3 — Application Detail
4 — Finding Detail
5 — Dashboard

Reason:

Data quality drives trust
Trust drives adoption