Phase 0 Build Plan v1

System: Upgrade Impact Analysis Tool
Purpose: Establish the minimum viable technical foundation for deterministic intake, analysis lifecycle, and UI-aligned service scaffolding
Goal: Create a stable skeleton that can support Phase 1 without redesign

1. Phase 0 Objectives

By the end of Phase 0, we should have:

a repo structure that reflects product boundaries
database migration 001 in place
workflow state and enum definitions locked
core API stubs implemented
audit/state-transition plumbing working
seeded sample data for Oracle KBs and customer intake
frontend route shell for the primary UX
enough end-to-end flow to prove the skeleton is alive

This phase does not need full analysis logic.
It needs the rails.

2. Exit Criteria

Phase 0 is complete when all of the following are true:

Database schema v1 foundation tables created
Core enums/constants implemented
Intake draft can be created and retrieved
Validation endpoint exists and returns deterministic blocking/warning results
Analysis run can be created in stub mode
State transitions are persisted
Sample KB + customer data can be loaded
Frontend routes render against stubbed or seeded API responses

If those conditions are not met, Phase 1 starts on sand.

3. Recommended Repo Structure

This is the smallest clean structure I’d use.

upgrade-impact-tool/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   ├── core/
│   │   ├── models/
│   │   ├── services/
│   │   ├── repositories/
│   │   ├── workflows/
│   │   ├── schemas/
│   │   └── db/
│   ├── migrations/
│   ├── seeds/
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── routes/
│   │   ├── pages/
│   │   ├── components/
│   │   ├── services/
│   │   ├── types/
│   │   └── mocks/
│   └── tests/
├── docs/
│   ├── contracts/
│   ├── schemas/
│   ├── roadmap/
│   └── decisions/
└── scripts/

Why this shape:

keeps API separate from workflow logic
leaves room for deterministic service orchestration
supports a UI-first frontend without burying it in backend assumptions
preserves a documentation layer for governance artifacts

That separation matches the broader architecture approach where orchestration owns flow, modules own bounded behavior, and outputs remain auditable.

4. Phase 0 Work Packages

There are eight work packages.

WP-01 — Project Bootstrap

Tasks:

initialize repo
create backend service skeleton
create frontend app shell
add linting/formatting
add environment config templates
add local dev bootstrap script

Deliverables:

backend app starts
frontend app starts
health check works
basic local setup documented
WP-02 — Core Constants and Enums

Tasks:

define analysis_status
define finding_status
define review_status
define change_taxonomy
define severity
define impact_type
define environment_type

Deliverables:

single source of truth enum module
shared frontend types generated or mirrored

Rule:

Do this once. Do not let strings breed in the wild like rats.

WP-03 — Database Migration 001

This migration should create the minimum foundational tables only.

Tier 1 tables for Migration 001
customers
environments
customer_state_snapshots
customer_applications
customer_modules
kb_articles
kb_article_versions
change_records
analysis_runs
analysis_applications
analysis_findings
finding_evidence
state_transitions

These are the priority tables from the storage model and are enough to support the first real UI path.

Tasks:

create tables
create foreign keys
create required indexes
add created/updated timestamps
add content hash fields where defined

Deliverables:

migration_001_applied successfully
seed data can be inserted
rollback strategy documented
WP-04 — Seed Data Package

We need deterministic sample data before real ingestion.

Tasks:

create 3 sample Oracle KB articles
create 1 version each for baseline
create 5–10 sample normalized change records
create 1 customer
create 1 production environment
create 1 snapshot
create 2 applications
create sample findings/evidence linked to the change records

Suggested scenario:

Customer: Acme Health
Environment: Production

Applications:
- Accounts Payable
- Payroll

Purpose:

power frontend development
power endpoint testing
validate joins and UI shape
support demo of early flows

Deliverables:

seed_001 loads cleanly
sample dashboard returns meaningful data
finding detail has KB evidence
WP-05 — API Skeleton v1

Implement only the minimum Tier 1 endpoints first.

Required endpoints for Phase 0
POST /api/v1/intakes
PATCH /api/v1/intakes/{intake_id}
POST /api/v1/intakes/{intake_id}/validate
GET /api/v1/intakes/{intake_id}
POST /api/v1/intakes/{intake_id}/analyses
GET /api/v1/analyses/{analysis_id}/status
GET /api/v1/dashboard
GET /api/v1/analyses/{analysis_id}
GET /api/v1/analyses/{analysis_id}/applications/{analysis_application_id}
GET /api/v1/findings/{finding_id}

These are the Tier 1 endpoints from the service contract and are enough to support intake, analysis lifecycle, overview, application detail, and finding detail.

Tasks:

implement route stubs
wire request/response schemas
return seeded data where logic is not complete
enforce standard error envelope
validate enum usage in responses

Deliverables:

OpenAPI or equivalent contract published
all Tier 1 endpoints callable locally
response shapes stable
WP-06 — Workflow and Audit Skeleton

This is the part people always want to “do later,” and then later arrives with a knife.

Tasks:

implement state transition service
log transitions to state_transitions
create analysis stub workflow:
DRAFT
INTAKE_VALIDATED
ANALYSIS_RUNNING
ANALYSIS_COMPLETE
REVIEW_REQUIRED
BLOCKED
prevent invalid transitions
ensure new analysis records are immutable once completed

Deliverables:

state changes recorded deterministically
invalid transition attempts rejected
analysis status visible through API

This follows the architectural rule that control logic should be explicit, centrally owned, and not hidden in ad hoc runtime behavior.

WP-07 — Frontend Route Shell

We are not building polished UI yet. We are building aligned surfaces.

Required routes for Phase 0
/dashboard
/intakes/new
/intakes/:id
/analyses/:id
/analyses/:id/applications/:applicationId
/findings/:id

Tasks:

create page shells
connect to seeded or stubbed endpoints
render loading state
render empty state
render error state
render primary layout regions based on spec

Deliverables:

user can click through core flow
pages load with sample data
layout proves IA and API contract alignment

This is important because the UI direction is explicitly about clear flow, visible evidence, and minimal clutter, not dense admin sludge.

WP-08 — Phase 0 Technical Decision Log

Tasks:

create docs/decisions/
log initial implementation decisions
log deferred items
log known gaps explicitly

Required ADR-style entries:

backend framework choice
frontend framework choice
migration tool choice
auth approach for Phase 0
seed-data strategy
response contract ownership
shared type strategy between frontend/backend

Deliverables:

decision log exists
deferred work is explicit
future sessions do not reinvent settled choices
5. Suggested Build Order

This is the safest sequence.

Day/Step Order
WP-01 Project Bootstrap
WP-02 Core Constants and Enums
WP-03 Database Migration 001
WP-04 Seed Data Package
WP-05 API Skeleton v1
WP-06 Workflow and Audit Skeleton
WP-07 Frontend Route Shell
WP-08 Decision Log

Reason:

constants before schema
schema before seed
seed before API
API before UI
audit before anyone gets cute
6. Concrete Task List

Here’s the actual punch list.

Backend Tasks
Create backend app skeleton
Add health check endpoint
Create enum/constants module
Create migration_001
Create seed_001
Create intake request/response schemas
Create analysis request/response schemas
Create findings response schemas
Implement intake routes
Implement analysis routes
Implement dashboard/results routes
Implement state transition service
Implement standard error envelope
Add basic repository layer
Add basic service layer
Frontend Tasks
Create app shell and router
Create API client wrapper
Create typed service interfaces
Create Dashboard page shell
Create Intake page shell
Create Results Overview page shell
Create Application Detail page shell
Create Finding Detail page shell
Create loading/error/empty components
Wire seeded responses to pages
Docs Tasks
Write local setup doc
Write migration runbook
Write seed runbook
Write decision log entry 001–007
Write endpoint contract summary
7. Minimum Testing Scope

Phase 0 does not need heroic testing, but it does need sane testing.

Required tests
Backend
migration applies
seed loads
create intake works
validate intake returns blocked on missing required fields
start analysis creates analysis record
invalid state transition fails
finding detail always includes KB reference
Frontend
routes render
dashboard displays seeded analysis
intake page handles empty and validation states
finding detail shows KB citation block

That last one matters because visible provenance is part of the product promise, not garnish.

8. What Not to Build in Phase 0

Do not build these yet:

real KB parser
real delta refresh engine
review queue workflow
export engine
notification system
admin screens
auth perfection
bulk upload parsing beyond placeholders
full matching logic

Why:

Because none of those help us prove the skeleton if intake, results, and finding detail are not aligned first.

9. Phase 0 Demo Script

By the end of Phase 0, you should be able to show this:

Open Dashboard
Show sample analysis card
Open Results Overview
Open one Application Detail
Open one Finding Detail
Show KB article number, title, link, and evidence
Show intake draft creation flow
Show blocked validation on missing required field
Show analysis state transition logged in audit view or backend response

That is enough to prove the system is real without pretending the hard parts are already finished.

10. Risks in Phase 0
Risk 1

Backend structure gets overbuilt before user path is visible.

Mitigation:

keep to Tier 1 tables/endpoints only
Risk 2

Frontend shells drift from API response shape.

Mitigation:

use seeded real responses, not invented mock JSON from a random afternoon delusion
Risk 3

Workflow logic leaks into controllers/routes.

Mitigation:

keep transition rules in a workflow/state service
Risk 4

Seed data too thin to validate UX.

Mitigation:

include at least one blocked item, one applies item, one review-required item
11. Recommended Definition of Done

Phase 0 is done when:

repo starts locally
DB migration and seed run cleanly
Tier 1 endpoints work
frontend route shells render real seeded data
one analysis lifecycle can be demonstrated
one finding detail view proves KB-backed traceability
transition audit exists
known gaps are documented, not “remembered”