# Frontend Recovery Runbook

## Purpose

Recover the frontend when Vite fails to compile, the app crashes at runtime, or priority pilot pages fail to render.

---

## Common Failure Cases

- JSX / TSX syntax error,
- stale dependency install,
- local cache issue,
- route-level runtime exception,
- API reachable but UI not rendering correctly.

---

## Recovery Procedure

### 1. Stop the frontend process
Stop the current Vite process.

### 2. Reinstall dependencies
From `frontend/`:

```bash
npm install
3. Restart the frontend

From frontend/:

npm run dev
4. Load the priority screens

Verify:

login,
dashboard,
create intake,
analysis overview,
review queue,
review item detail,
admin inspection.
5. If compile error appears
capture the exact file and line,
fix the syntax issue,
restart Vite,
reload the failing page.
6. If runtime error appears
capture the exact screen and action,
check browser console,
verify backend health,
retry after a full page refresh.
Escalate Immediately If
login page does not load,
dashboard does not render,
admin inspection is required for the pilot and fails,
multiple priority routes fail after restart.

If the UI cannot be trusted, do not proceed with the pilot.