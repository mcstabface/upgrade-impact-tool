# Gate 16A Production Auth Design Spec

System: Upgrade Impact Analysis Tool  
Phase: Production Auth / Role Guard Design  
Status: Design-only security gate  
Generated: 2026-05-13

## Purpose

Gate 16A defines the production authentication, authorization, and audit-hardening design required before local review mutation is exposed beyond the prototype boundary.

Gate 15 proved that the local guarded endpoint can:

- require reviewer identity,
- authorize reviewer role from a local policy file,
- reject observer mutation,
- reject missing request provenance,
- record request provenance in audit events,
- preserve Gate 10/Gate 12/Gate 13 validation behavior,
- keep finalization disabled.

Gate 16A deliberately does **not** replace Gate 15 implementation. It defines the production controls that must exist before browser mutation or shared deployment is treated as safe.

## Scope

This design applies to review mutation paths for:

- claim decision updates,
- visual-review acknowledgements,
- unresolved-gap acknowledgements,
- future finalization preflight or finalization workflows.

This design covers:

- identity provider integration,
- authenticated principal mapping,
- role and permission model,
- signed or trusted request validation,
- request provenance,
- audit hardening,
- authorization failure behavior,
- secrets and configuration boundaries,
- production readiness gates.

This design does not implement production authentication in code.

## Current Local Baseline

Current local mutation path:

```text
Browser/future client
  -> guarded local HTTP endpoint
  -> Gate 15 authorization/provenance guard
  -> Gate 13 review update service
  -> Gate 12 mutation bridge
  -> Gate 10 update functions and validators
  -> regenerated reviewer artifacts
```

Current local policy artifact:

```text
kbs/policies/review_authorization_policy.v1.json
```

Current local guarded endpoint:

```text
backend/app/scripts/guarded_review_update_http_server.py
```

Current local provenance validator:

```text
backend/app/scripts/validate_kb_review_provenance.py
```

Gate 15 is explicitly local-development authorization. It is not production auth.

## Production Auth Target Architecture

Production mutation requests must use this sequence:

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

The production auth layer must sit before review mutation. It must reject unauthorized requests before the Gate 13 service contract is invoked.

## Identity Provider Requirements

The production deployment must choose one identity provider pattern before enabling shared mutation:

| Pattern | Use Case | Notes |
|---|---|---|
| OIDC interactive login | Browser-based reviewer workflow | Preferred for human reviewers. |
| Reverse-proxy asserted identity | Internal deployment behind trusted gateway | Requires signed/trusted headers and strict network boundary. |
| Signed service token | Automation or service-to-service mutation | Must be scoped and auditable. |

Required authenticated principal fields:

- immutable subject ID,
- display name,
- email or username,
- issuer,
- authentication method,
- session/request expiration,
- group or role claims if available.

Do not rely on client-supplied reviewer ID as the sole identity source in production.

## Reviewer Identity Mapping

Production reviewer identity must be derived from authenticated principal data, not plain request body text.

Required mapping:

```text
authenticated principal -> reviewer identity -> role assignments -> allowed review actions
```

The request body may include a reviewer display hint, but production authorization must ignore it for permission decisions.

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

No production role should imply finalization until a dedicated finalization workflow exists.

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
9. finalization remains disabled unless future finalization gate enables it.

Rejected requests must not create mutation audit events. They may create separate security audit events.

## Trusted Request Validation

Production must use one of these request trust mechanisms:

### OIDC session

- Validate session using server-side session store or signed encrypted cookie.
- Enforce CSRF protection for browser mutation.
- Use SameSite cookie controls.
- Tie session to issuer and subject.

### Reverse-proxy identity headers

- Accept identity headers only from trusted proxy network path.
- Require signed headers or mTLS between proxy and app.
- Reject identity headers from direct client traffic.
- Record proxy identity source in provenance.

### Signed service token

- Validate signature.
- Validate issuer/audience.
- Validate expiration.
- Validate action scope.
- Record token subject and key ID in provenance.

## Request Provenance Requirements

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

Gate 15 currently records a local subset. Production must extend this before broad browser mutation.

## Audit Hardening

Production audit events must be append-only at the application level.

Audit event requirements:

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

## Configuration and Secrets

Production auth configuration must not live in generated KB artifacts.

Allowed local prototype config:

```text
kbs/policies/review_authorization_policy.v1.json
```

Production config should move to deployment-managed configuration:

- environment variables for issuer/audience/client IDs,
- secret manager for client secrets/signing keys,
- deployment config for trusted proxy networks,
- external role mapping source or admin-managed policy store.

Never commit production secrets.

## Failure Behavior

Authorization failures must fail closed.

Required response behavior:

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

## Production Readiness Gates

Before production/shared deployment mutation is enabled, these gates must pass:

| Gate | Required Proof |
|---|---|
| Auth integration | authenticated principal cannot be spoofed from request body |
| Role enforcement | observer cannot mutate |
| Provenance | mutation audit includes principal, role, request ID, source, and policy version |
| Validation | Gate 10/Gate 12 validators run after mutation |
| Audit | mutation audit and security denial audit are recorded |
| Browser safety | no direct JSON mutation from browser code |
| Finalization control | finalization remains disabled |

## Migration Path from Gate 15

Recommended migration path:

1. Keep Gate 15 local policy for smoke tests.
2. Add production auth adapter interface:
   - `get_authenticated_principal(request)`
   - `map_principal_to_reviewer(principal)`
   - `authorize_action(reviewer, action)`
3. Add security audit events for denied requests.
4. Extend provenance schema to include principal and policy version.
5. Add endpoint tests for:
   - unauthenticated request,
   - observer request,
   - reviewer claim update,
   - reviewer gap update,
   - missing visual acknowledgement,
   - missing CSRF/request ID.
6. Only then bind browser mutation to the guarded endpoint.

## Gate 16A Acceptance Criteria

Gate 16A is complete when:

1. production auth design spec exists,
2. local Gate 15 is explicitly identified as non-production auth,
3. production identity provider options are documented,
4. reviewer identity mapping requirements are documented,
5. role model is documented,
6. permission checks are documented,
7. trusted request validation requirements are documented,
8. production provenance requirements are documented,
9. audit hardening plan is documented,
10. browser mutation requirements are documented,
11. production readiness gates are documented,
12. next implementation gate is clearly defined.

## Recommended Next Gate

Recommended next gate after Gate 16A:

**Gate 16B — Auth Adapter Interface and Security Audit Events**

Gate 16B should add code-level interfaces without committing to a provider:

- authenticated principal dataclass,
- reviewer identity dataclass,
- auth adapter protocol,
- local policy adapter implementation,
- security denial audit JSONL writer,
- tests/smoke runner for authorized and denied requests.

Do not proceed directly to broad browser mutation until security denial auditing and principal-derived reviewer identity exist.
