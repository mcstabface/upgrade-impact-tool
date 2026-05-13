# Gate 16A Production Auth Design Build Plan

System: Upgrade Impact Analysis Tool  
Phase: Production Auth / Role Guard Design  
Status: Design-only security gate  
Generated: 2026-05-13

## Starting Point

Gate 1 completed KB source extraction and PFDS evidence mapping.

Gate 2 completed matched PFDS source text extraction and deterministic chunking.

Gate 3 completed deterministic lexical retrieval over PFDS chunks.

Gate 4 completed retrieval diagnostics and controls.

Gate 5 completed deterministic BM25 ranking and retrieval evaluation.

Gate 6 completed evidence-only impact context assembly.

Gate 7 completed impact context enrichment and draft skeleton.

Gate 8 completed constrained citation-bound impact draft generation.

Gate 9 completed draft review workflow and reviewer export.

Gate 10 completed review decision update commands.

Gate 11 completed read-only review UI surface.

Gate 12 completed mutation bridge with audit trail and artifact regeneration.

Gate 13 completed review update service contract.

Gate 14 completed local HTTP review update endpoint.

Gate 15 completed auth/role guard and request provenance for local endpoint.

Current Gate 15 baseline:

- guarded endpoint supports `GET /health`
- guarded endpoint supports `POST /review/update`
- authorization policy exists for reviewer/observer roles
- authorized reviewer mutation succeeds
- observer mutation is denied before mutation
- missing request ID is rejected before mutation
- authorized mutation records request provenance in audit event
- audit trail validates with `[gate12:audit] OK`
- provenance validates with `[gate15:provenance] OK`
- mutable review state validates with `[gate10:validate] OK`
- regenerated guarded surface validates with `[gate11:validate] OK`
- finalization remains disabled

## Gate 16A Objective

Gate 16A answers this bounded question:

> What production authentication, authorization, request provenance, and audit-hardening controls are required before browser mutation or shared deployment is treated as safe?

Gate 16A is design-only. It does not implement production auth.

## First Implementation Slice

Added:

| File | Purpose |
|---|---|
| `docs/security/Gate 16A Production Auth Design Spec.md` | Production auth, authorization, provenance, and audit-hardening design. |
| `backend/app/scripts/validate_gate16a_production_auth_design.py` | Coverage validator for the design spec. |
| `backend/app/scripts/run_gate16a_production_auth_design.py` | Runs Gate 16A validation. |

## Design Coverage

The spec covers:

- local Gate 15 baseline and limitations,
- production auth target architecture,
- identity provider options,
- reviewer identity mapping,
- production role model,
- permission checks,
- trusted request validation,
- production request provenance,
- audit hardening,
- configuration and secrets boundaries,
- failure behavior,
- browser mutation requirements,
- production readiness gates,
- migration path from Gate 15,
- recommended Gate 16B.

## Run Commands

From backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate16a_production_auth_design
```

Dry run:

```bash
python -m app.scripts.run_gate16a_production_auth_design --dry-run
```

## Acceptance Criteria

Gate 16A initial slice is complete when:

1. `python -m app.scripts.run_gate16a_production_auth_design` completes successfully.
2. Validator passes with `[gate16a:validate] OK`.
3. Production auth design spec exists.
4. Local Gate 15 is explicitly identified as non-production auth.
5. Identity provider options are documented.
6. Reviewer identity mapping requirements are documented.
7. Role model is documented.
8. Permission checks are documented.
9. Trusted request validation requirements are documented.
10. Production provenance requirements are documented.
11. Audit hardening plan is documented.
12. Browser mutation requirements are documented.
13. Production readiness gates are documented.
14. Next implementation gate is clearly defined.

## Non-Goals

Gate 16A does not:

- implement OIDC,
- implement enterprise identity integration,
- implement production auth middleware,
- expose browser mutation,
- change Gate 15 local guarded endpoint behavior,
- finalize drafts,
- call an LLM.

## Recommended Next Gate

Recommended next gate:

**Gate 16B — Auth Adapter Interface and Security Audit Events**

Gate 16B should add code-level interfaces without committing to a production provider:

- authenticated principal dataclass,
- reviewer identity dataclass,
- auth adapter protocol,
- local policy adapter implementation,
- security denial audit JSONL writer,
- smoke runner for authorized and denied requests.

Do not proceed directly to broad browser mutation until security denial auditing and principal-derived reviewer identity exist.

## Notes

Gate 16A exists because Gate 15 is a local doorman, not a security architecture. This distinction matters, regrettably, because doors are where trouble keeps entering.
