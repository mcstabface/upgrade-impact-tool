# Gate 16A Production Auth Design Completion Artifact

System: Upgrade Impact Analysis Tool  
Phase: Production Auth / Role Guard Design  
Status: Complete for current design gate  
Generated: 2026-05-13

## Purpose

This checkpoint captures the completed state of Gate 16A for the KB ingestion/customization phase.

Gate 16A answered this bounded question:

> What production authentication, authorization, request provenance, and audit-hardening controls are required before browser mutation or shared deployment is treated as safe?

For the current design gate, the answer is documented and validated.

Gate 16A is design-only. It does not implement production authentication, enterprise identity integration, browser mutation, finalization, or LLM-assisted review decisions.

## Source Baseline

Gate 16A starts from Gate 15 auth/role guard and request provenance for the local endpoint.

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

Gate 15 remains explicitly local-development authorization, not production auth.

## Gate 16A Pipeline

Run from backend:

```bash
cd /home/stabby/Documents/upgrade-impact-tool/backend
source .venv/bin/activate
python -m app.scripts.run_gate16a_production_auth_design
```

Dry run:

```bash
python -m app.scripts.run_gate16a_production_auth_design --dry-run
```

The runner executes:

```text
app.scripts.validate_gate16a_production_auth_design
```

## Generated / Updated Artifacts

| Artifact | Purpose |
|---|---|
| `docs/security/Gate 16A Production Auth Design Spec.md` | Production auth, authorization, provenance, and audit-hardening design |
| `backend/app/scripts/validate_gate16a_production_auth_design.py` | Coverage validator for the design spec |
| `backend/app/scripts/run_gate16a_production_auth_design.py` | Runs Gate 16A validation |
| `docs/checkpoints/Gate 16A Production Auth Design Build Plan.md` | Build plan and acceptance criteria for Gate 16A |

## Latest Verified Pipeline Output

Local clean run completed successfully with:

```text
python -m app.scripts.run_gate16a_production_auth_design
```

Validation:

```text
[gate16a:validate] OK
```

## Design Scope

The design spec covers review mutation paths for:

- claim decision updates,
- visual-review acknowledgements,
- unresolved-gap acknowledgements,
- future finalization preflight or finalization workflows.

The design covers:

- identity provider integration,
- authenticated principal mapping,
- role and permission model,
- signed or trusted request validation,
- request provenance,
- audit hardening,
- authorization failure behavior,
- secrets and configuration boundaries,
- production readiness gates.

## Production Auth Target Architecture

The documented production target sequence is:

```text
Client action
  -> authenticated session or signed service request
  -> production auth middleware
  -> principal extraction
  -> role/permission resolution
  -> request provenance construction
  -> Gate 13 service request construction
  -> Gate 12 mutation bridge
  -> Gate 10 review-state validation
  -> audit append
  -> artifact/state regeneration
  -> response to client
```

The production auth layer must sit before review mutation and reject unauthorized requests before the Gate 13 service contract is invoked.

## Identity Provider Options

The design documents three acceptable production identity provider patterns:

| Pattern | Use Case |
|---|---|
| OIDC interactive login | Browser-based reviewer workflow |
| Reverse-proxy asserted identity | Internal deployment behind trusted gateway |
| Signed service token | Automation or service-to-service mutation |

Required authenticated principal fields include:

- immutable subject ID,
- display name,
- email or username,
- issuer,
- authentication method,
- session/request expiration,
- group or role claims if available.

The design explicitly states that production must not rely on client-supplied reviewer ID as the sole identity source.

## Reviewer Identity Mapping

Production reviewer identity must be derived from authenticated principal data, not plain request body text.

Required mapping:

```text
authenticated principal -> reviewer identity -> role assignments -> allowed review actions
```

Required reviewer identity fields:

- `principal_subject`,
- `principal_issuer`,
- `reviewer_id`,
- `reviewer_display_name`,
- `reviewer_email_or_username`,
- `roles`,
- `status`.

## Role Model

Minimum production roles:

| Role | Description | Allowed Actions |
|---|---|---|
| `review_observer` | Can view review artifacts only | none |
| `reviewer` | Can update claim decisions and gap acknowledgements | claim, gap |
| `lead_reviewer` | Can complete review preflight once all requirements are satisfied | claim, gap, review_complete_preflight |
| `admin` | Can manage role mappings and policy config | role_admin, policy_admin |

Finalization remains disabled until a later explicit finalization gate.

## Permission Checks

Every mutation request must check:

1. requester is authenticated,
2. session/token is unexpired,
3. principal maps to active reviewer identity,
4. reviewer has at least one active role,
5. role allows requested action,
6. action is compatible with current review state,
7. visual acknowledgement is present for accepted image-bearing claims,
8. request provenance is complete,
9. finalization remains disabled unless a future finalization gate enables it.

Rejected requests must not create mutation audit events. They may create separate security audit events.

## Trusted Request Validation

The design documents requirements for:

- OIDC session validation,
- reverse-proxy asserted identity headers,
- signed service tokens.

Required production safeguards include CSRF protection for browser mutation, trusted proxy boundaries for asserted identity headers, and signature/issuer/audience/expiration/scope validation for service tokens.

## Production Provenance Requirements

Production provenance must include:

- request ID,
- correlation ID if available,
- endpoint route,
- HTTP method,
- authenticated principal subject,
- principal issuer,
- reviewer ID,
- reviewer role(s),
- source IP or trusted forwarded source,
- user agent,
- auth method,
- policy version,
- decision reason,
- mutation target ID,
- mutation action,
- timestamp UTC.

Gate 15 records only a local subset. Gate 16A requires production provenance to extend that subset before broad browser mutation.

## Audit Hardening

The design requires production audit events to be append-only at the application level.

Audit event requirements include:

- unique event ID,
- monotonic sequence or timestamp,
- actor identity,
- role at time of action,
- request provenance,
- previous target state,
- new target state,
- validation result,
- policy version,
- auth method,
- denial reason for security audit events,
- tamper-evident hash chain if audit leaves local prototype mode.

Recommended audit hardening sequence:

1. add security audit event stream separate from review mutation audit,
2. add immutable append-only JSONL artifact locally,
3. add hash chaining across audit records,
4. ship audit records to central logging in deployment mode,
5. retain review manifest audit as reviewer-facing summary only.

## Failure Behavior

The design requires auth and authorization failures to fail closed.

Required failure behavior:

| Failure | Response |
|---|---|
| Missing auth | 401 Unauthorized |
| Invalid/expired auth | 401 Unauthorized |
| Authenticated but insufficient role | 403 Forbidden |
| Missing provenance | 400 Bad Request |
| Invalid request payload | 400 Bad Request |
| Mutation validation failure | 409 Conflict or 422 Unprocessable Entity |
| Internal error | 500 with generic client message and detailed server log |

All failure responses must report:

```text
finalization_allowed = false
```

## Browser Mutation Requirements

Browser mutation must not write JSON files directly.

Browser action must call a server-side endpoint that:

1. validates authenticated session,
2. derives reviewer identity server-side,
3. validates role/action permission,
4. constructs Gate 13 request,
5. calls Gate 13/Gate 12 path,
6. validates review state,
7. records provenance,
8. regenerates reviewer artifacts or updates state store,
9. returns structured response.

Required browser request safeguards:

- CSRF token or same-origin POST protection,
- request ID generation,
- clear mutation confirmation for accepted claims,
- visual-review acknowledgement checkbox for image-bearing evidence,
- no finalization controls until later gate.

## Validation Coverage

The Gate 16A validator checks that the spec includes:

- Gate 16A title and scope,
- explicit Gate 15 local-only/non-production boundary,
- identity provider requirements,
- reviewer identity mapping,
- role model,
- permission checks,
- trusted request validation,
- request provenance requirements,
- audit hardening,
- configuration and secrets boundaries,
- failure behavior,
- browser mutation requirements,
- production readiness gates,
- migration path from Gate 15,
- Gate 16B recommendation,
- OIDC / reverse-proxy / signed service-token options,
- required production roles,
- required failure response classes,
- finalization-disabled language,
- direct JSON mutation prohibition,
- warning against client-supplied reviewer ID as sole production identity source.

## What This Proves

Gate 16A proves that the project now has a documented and validated production-auth design boundary before proceeding to broader browser mutation or shared deployment mutation.

It specifically prevents conflating:

```text
local Gate 15 policy file auth
```

with:

```text
production authentication and authorization
```

Astonishingly, writing down that a cardboard badge is not an identity provider remains necessary work.

## Known Limitations

Gate 16A is design-only.

Known limitations:

- It does not implement OIDC.
- It does not implement reverse-proxy identity trust.
- It does not implement signed service tokens.
- It does not implement production auth middleware.
- It does not implement security denial audit events.
- It does not expose browser mutation.
- It does not finalize drafts.
- It does not call an LLM.

These limitations are acceptable for Gate 16A. They define the next gate.

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

## Recommended Next Chat Starting Point

Use this prompt to continue in a new chat:

```text
We are continuing work on the Upgrade Impact Analysis Tool.

Gate 1 completed KB source extraction and PFDS evidence mapping.
Gate 2 completed KB PFDS source text extraction and deterministic chunking.
Gate 3 completed KB PFDS lexical retrieval index and query.
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
Gate 16A completed production auth design spec.

Use this repo as source of truth:
mcstabface/upgrade-impact-tool

Start from these docs/artifacts:
- docs/checkpoints/Gate 1 KB Source Extraction Completion Artifact.md
- docs/checkpoints/Gate 2 KB Search Context Completion Artifact.md
- docs/checkpoints/Gate 3 KB PFDS Retrieval Completion Artifact.md
- docs/checkpoints/Gate 4 KB Retrieval Diagnostics Completion Artifact.md
- docs/checkpoints/Gate 5 BM25 Ranking Evaluation Completion Artifact.md
- docs/checkpoints/Gate 6 Impact Context Assembly Completion Artifact.md
- docs/checkpoints/Gate 7 Impact Context Enrichment Completion Artifact.md
- docs/checkpoints/Gate 8 Constrained Impact Draft Completion Artifact.md
- docs/checkpoints/Gate 9 Draft Review Workflow Completion Artifact.md
- docs/checkpoints/Gate 10 Review Decision Update Commands Completion Artifact.md
- docs/checkpoints/Gate 11 Review UI Surface Completion Artifact.md
- docs/checkpoints/Gate 12 UI Mutation Bridge Completion Artifact.md
- docs/checkpoints/Gate 13 Live Review API Completion Artifact.md
- docs/checkpoints/Gate 14 Actual API Endpoint Completion Artifact.md
- docs/checkpoints/Gate 15 Auth Role Guard Completion Artifact.md
- docs/checkpoints/Gate 16A Production Auth Design Completion Artifact.md
- docs/security/Gate 16A Production Auth Design Spec.md
- backend/app/scripts/run_gate16a_production_auth_design.py
- backend/app/scripts/validate_gate16a_production_auth_design.py

Current Gate 16A status:
- production auth design spec exists
- local Gate 15 is explicitly scoped as non-production auth
- OIDC, reverse-proxy identity, and signed service-token patterns are documented
- reviewer identity must be derived from authenticated principal data in production
- production role model is documented
- permission checks are documented
- production provenance requirements are documented
- audit hardening requirements are documented
- browser mutation requirements are documented
- production readiness gates are documented
- validator passes with `[gate16a:validate] OK`
- finalization remains disabled

The Gate 16A pipeline runs successfully with:
python -m app.scripts.run_gate16a_production_auth_design

Next recommended gate is Gate 16B: Auth Adapter Interface and Security Audit Events.

Please review the repo and produce the next concrete build plan and first patches for Gate 16B.
Be specific, repo-grounded, and provide exact patch contents.
```

## Completion Status

Gate 16A is complete for the current design gate.

The next work should begin from this checkpoint, not from memory.
