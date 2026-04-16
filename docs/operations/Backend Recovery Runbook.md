# Backend Recovery Runbook

## Purpose

Recover the backend when it fails to start, fails health checks, or behaves inconsistently during pilot use.

---

## Common Failure Cases

- dependency install incomplete,
- startup exception during import,
- migration/schema drift,
- auth/session regression,
- local database unavailable,
- wrong environment configuration.

---

## Recovery Procedure

### 1. Stop the backend process
Stop the current Uvicorn process before retrying.

### 2. Confirm dependencies
From `backend/` with the virtual environment active:

```bash
pip install -r requirements.txt
3. Confirm database reachability

Verify the configured database is reachable and intended.

4. Start the backend again

From backend/:

uvicorn app.main:app --reload
5. Check health

Open:

http://127.0.0.1:8000/api/v1/health

Expected response:

{"status":"ok"}
6. Re-seed pilot users if auth state is suspect

From backend/:

python -m app.scripts.seed_pilot_users
7. Run environment verification

From backend/:

python -m app.scripts.verify_pilot_environment
Escalate Immediately If
the backend still fails to boot,
/api/v1/health does not return 200,
login fails after reseeding users,
database state is unknown.

At that point, use Pilot Reset Procedure.md.