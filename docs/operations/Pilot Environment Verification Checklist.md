# Pilot Environment Verification Checklist

## Purpose

This checklist verifies that the current local or pilot environment is coherent before pilot use.

Use this after:
- pulling latest changes,
- applying migrations,
- reseeding pilot users,
- restoring a database snapshot,
- or whenever the environment feels even slightly cursed.

---

## Required Commands

Run these from the repo root unless noted otherwise.

### 1. Backend dependency check
From `backend/` with the virtual environment active:

```bash
pip install -r requirements.txt
2. Start backend

From backend/:

uvicorn app.main:app --reload
3. Start frontend

From frontend/:

npm install
npm run dev
4. Run pilot auth seed

From backend/:

python -m app.scripts.seed_pilot_users
5. Run pilot environment verification

From backend/:

python -m app.scripts.verify_pilot_environment

Expected result:

Pilot environment verification passed.
Manual Verification
Authentication
 Login page renders.
 Login works with pilot.admin@example.com.
 Logout works.
 Reloading the app preserves the authenticated session.
 Opening the app in a fresh session redirects to login.
Priority Screens
 Dashboard renders.
 Create Intake renders for analyst/admin.
 Analysis Overview renders.
 Review Queue renders.
 Review Item Detail renders.
 Admin Inspection renders for admin.
Export Checks
 Analysis JSON export downloads successfully.
 Review queue CSV export downloads successfully.
Admin Checks
 Admin inspection loads observability summary.
 Admin inspection can inspect audit/lineage for a selected analysis.
Failure Handling

If any verification step fails:

Stop the pilot.
Record the failing step exactly.
Capture the console or backend error text.
Use Pilot Reset Procedure.md if the state is suspect.
Re-run this checklist from the top.

Do not improvise your own "quick fix" during a live pilot unless the fix is already documented and reversible.


---

# 4) Add pilot reset procedure

## New file
`docs/operations/Pilot Reset Procedure.md`

```md
# Pilot Reset Procedure

## Purpose

Use this procedure when the pilot environment is no longer trusted.

Examples:
- the database state is unknown,
- pilot data has been mutated in a way that breaks the walkthrough,
- auth/session behavior is inconsistent,
- seeded users are missing or corrupted,
- the operator is no longer sure what state the system is in.

When that happens, stop pretending and reset the environment deliberately.

---

## Reset Principles

1. Prefer a known-good restore point over ad hoc manual cleanup.
2. Re-seed pilot auth users after restore.
3. Re-run environment verification after reset.
4. Do not resume pilot work until verification passes.

---

## Standard Reset Flow

### 1. Stop the frontend and backend
Stop the running processes so no one is writing into the environment during reset.

### 2. Restore the known-good database snapshot
Restore the database snapshot that has been approved as the pilot baseline.

The exact restore command depends on how the local or pilot database backup was created.
Use your approved restore method here.

Required outcome:
- the schema is current,
- the dataset is intentional,
- the restore completes without errors.

### 3. Re-apply the pilot auth schema if needed
If the restored snapshot predates auth hardening, re-apply the auth schema.

Example:

```bash
psql postgresql://postgres:postgres@localhost:5432/upgrade_impact_tool -f backend/sql/001_pilot_auth.sql
4. Re-seed pilot users

From backend/:

python -m app.scripts.seed_pilot_users
5. Restart backend

From backend/:

uvicorn app.main:app --reload
6. Restart frontend

From frontend/:

npm run dev
7. Run environment verification

From backend/:

python -m app.scripts.verify_pilot_environment
8. Re-run the pilot checklist

Use:

Pilot Environment Verification Checklist.md
Pilot Go-No-Go Checklist.md

Do not call the environment reset until both pass.

Minimum Reset Acceptance Criteria

A reset is complete only when:

seeded pilot users can log in,
/api/v1/health returns 200,
/api/v1/auth/me returns 401 before login,
/api/v1/auth/me returns 200 after login,
dashboard loads,
admin inspection loads,
the dataset shown in the UI matches the intended pilot baseline.
If Reset Fails

If the reset does not restore a trustworthy environment:

declare NO-GO,
stop the pilot,
capture the error,
escalate using Pilot Support Ownership and Triage.md.

The wrong recovery is worse than a delay.


---

# 5) Add support ownership and triage doc

## New file
`docs/operations/Pilot Support Ownership and Triage.md`

```md
# Pilot Support Ownership and Triage

## Purpose

Define who owns what during pilot operation and how to respond when something breaks.

A pilot fails faster when everyone assumes someone else is holding the wrench.

---

## Roles

### Pilot Operator
Owns:
- running the checklists,
- starting frontend and backend,
- verifying seeded users,
- confirming the intended pilot dataset is loaded,
- deciding whether the environment is GO or NO-GO.

### Technical Owner
Owns:
- backend failures,
- auth failures,
- database/reset failures,
- frontend build/runtime failures,
- recovery execution when the operator cannot safely restore service.

### Pilot Stakeholder / Facilitator
Owns:
- user communications,
- expectation management,
- deciding whether to pause, reschedule, or continue with reduced scope.

---

## Incident Severity

### Severity 1 — Pilot blocking
Examples:
- backend will not start,
- login is broken,
- dashboard will not load,
- admin inspection fails when it is required for the pilot,
- database state is unknown.

Action:
- stop the pilot flow,
- declare NO-GO unless recovery is immediate and verified,
- escalate to the technical owner.

### Severity 2 — Feature degraded but pilot can continue
Examples:
- export fails,
- one admin-only inspection detail is unavailable,
- a non-critical screen has a layout problem but primary workflow still works.

Action:
- log the issue,
- use workaround if documented,
- continue only if stakeholder agrees the pilot objective is still intact.

### Severity 3 — Cosmetic or low-risk issue
Examples:
- minor spacing issue,
- copy inconsistency,
- low-priority display bug with no workflow impact.

Action:
- log it,
- do not derail the pilot for it.

---

## Triage Steps

1. Capture the failing action exactly.
2. Capture the error message exactly.
3. Identify severity.
4. Decide:
   - continue,
   - recover,
   - reset,
   - or stop.
5. Record the outcome.

---

## Required Recovery References

When triaging, use:
- `Pilot Environment Verification Checklist.md`
- `Pilot Reset Procedure.md`
- `Pilot Go-No-Go Checklist.md`

Do not invent a new operating model in the middle of a pilot.

---

## Pilot Decision Rule

If authentication, route protection, or environment trust is in doubt, the default decision is **pause and verify**.

The system can survive bruised aesthetics.
It cannot survive uncertain trust.