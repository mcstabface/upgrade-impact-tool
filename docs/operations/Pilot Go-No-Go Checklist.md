# Pilot Go-No-Go Checklist

## Purpose

Use this checklist immediately before any pilot session, live demo, or stakeholder walkthrough.
Do not rely on memory.
Do not skip the checks because "it worked earlier."

A pilot is **GO** only if every blocking item below is complete.

---

## Blocking Checks

### 1. Backend availability
- [ ] Backend process is running.
- [ ] `GET /api/v1/health` returns `200` with `{"status":"ok"}`.
- [ ] No backend boot errors are present in the startup console.

### 2. Database and seed state
- [ ] The pilot auth schema has been applied.
- [ ] Pilot users have been seeded successfully.
- [ ] The current database is the intended pilot dataset, not an unknown local state.
- [ ] There is a known-good restore point or backup for the pilot database.

### 3. Authentication and role enforcement
- [ ] Login succeeds for `pilot.admin@example.com`.
- [ ] `GET /api/v1/auth/me` returns the authenticated user after login.
- [ ] `GET /api/v1/auth/me` returns `401` before login.
- [ ] Logout clears the session and `GET /api/v1/auth/me` returns `401` again.
- [ ] The dashboard loads only after login.
- [ ] The admin inspection view is accessible only to admin users.

### 4. Frontend availability
- [ ] Frontend process is running.
- [ ] The app loads without Vite compile errors.
- [ ] The login page renders.
- [ ] Dashboard, intake, analysis overview, review queue, review item detail, and admin inspection render without fatal runtime errors.

### 5. Core pilot flows
- [ ] Sign in as admin.
- [ ] Open dashboard.
- [ ] Open review queue.
- [ ] Open an existing analysis overview.
- [ ] Open an existing review item.
- [ ] Open admin inspection.
- [ ] Export analysis JSON from an analysis overview page.
- [ ] Export review queue CSV.

### 6. Operator readiness
- [ ] This checklist has been completed today.
- [ ] `Pilot Environment Verification Checklist.md` has been run.
- [ ] `Pilot Reset Procedure.md` is available and current.
- [ ] `Pilot Support Ownership and Triage.md` is available and current.
- [ ] The pilot operator knows who owns blocker triage.

---

## Recommended Non-Blocking Checks

- [ ] Browser cache/session is clean before the pilot starts.
- [ ] A second seeded user account is available for role-specific spot checks.
- [ ] The current pilot dataset contains at least:
  - one completed analysis,
  - one review queue item,
  - one analysis with lineage or stale/refresh behavior if admin inspection is being shown.
- [ ] Exported files download successfully in the pilot browser.

---

## Go / No-Go Decision

### GO
Use **GO** only if:
- every blocking check is complete,
- there are no unresolved auth issues,
- there are no compile/runtime errors on priority screens,
- the pilot dataset is known and intentional.

### NO-GO
Use **NO-GO** if any of the following are true:
- login/logout is broken,
- role enforcement is inconsistent,
- backend or frontend fails to start cleanly,
- priority pilot screens fail to render,
- the dataset is unknown,
- no recovery/reset path is available.

If **NO-GO**, stop and run the recovery or reset procedure before exposing the product to pilot users.