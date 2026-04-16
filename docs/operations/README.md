# Pilot Operations

This directory contains the minimum operational documents required before pilot use.

## Files

- `Pilot Go-No-Go Checklist.md`
- `Pilot Environment Verification Checklist.md`
- `Pilot Reset Procedure.md`
- `Pilot Support Ownership and Triage.md`
- `Backend Recovery Runbook.md`
- `Frontend Recovery Runbook.md`

## Recommended Order of Use

1. Run `Pilot Environment Verification Checklist.md`
2. Run `Pilot Go-No-Go Checklist.md`
3. If the environment is not trusted, use `Pilot Reset Procedure.md`
4. If a specific layer fails, use the relevant recovery runbook
5. If the issue affects pilot execution, use `Pilot Support Ownership and Triage.md`