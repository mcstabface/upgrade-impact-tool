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