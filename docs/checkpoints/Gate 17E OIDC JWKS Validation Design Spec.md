# Gate 17E OIDC JWKS Validation Design Spec

System: Upgrade Impact Analysis Tool  
Phase: Deterministic OIDC JWKS Validation Design  
Status: Proposed design spec  
Generated: 2026-05-13

## Purpose

Gate 17E defines the deterministic production-token validation design before implementation.

This gate answers:

> What exact constraints must a future OIDC/JWKS validator satisfy before it can be wired into the guarded review endpoint?

Gate 17E is a design gate only. It does not implement JWT signature validation, does not fetch JWKS, does not accept tokens, does not replace `LocalPolicyAuthAdapter`, and does not enable finalization.

## Source Baseline

Gate 17E starts from Gate 17D:

- OIDC adapter skeleton exists and fails closed.
- Bearer-token extraction exists for diagnostics only.
- Unsafe JWT parsing exists for diagnostics only.
- OIDC denial reason mapping exists.
- Disabled OIDC smoke harness writes valid security-denial audit events.
- Guarded endpoint remains on `LocalPolicyAuthAdapter`.
- Finalization remains disabled.

## Design Goals

A future OIDC validator must be:

- deterministic,
- fail-closed,
- auditable,
- explicitly configured,
- disabled by default,
- bounded to known issuers and audiences,
- strict about accepted algorithms,
- explicit about clock-skew handling,
- conservative about reviewer identity mapping,
- compatible with existing security-denial audit events.

## Non-Goals

Gate 17E does not design or permit:

- implicit tenant discovery,
- runtime trust of arbitrary issuer metadata,
- accepting unsigned tokens,
- accepting tokens before signature validation,
- accepting tokens before issuer/audience/time validation,
- accepting tokens without reviewer mapping,
- changing the review mutation contract,
- changing the security-denial audit schema,
- enabling finalization.

## Proposed Config Contract

Future config path:

```text
kbs/policies/review_oidc_adapter.config.json
```

Required production-enabled fields:

```json
{
  "enabled": true,
  "issuer": "https://issuer.example.test",
  "audience": "upgrade-impact-tool",
  "jwks_uri": "https://issuer.example.test/.well-known/jwks.json",
  "accepted_algorithms": ["RS256"],
  "clock_skew_seconds": 60,
  "reviewer_id_claim": "preferred_username",
  "display_name_claim": "name",
  "email_claim": "email",
  "groups_claim": "groups",
  "role_claim": "roles",
  "required_groups": ["upgrade-impact-reviewers"],
  "jwks_cache_ttl_seconds": 3600,
  "require_kid": true
}
```

No production config should be committed unless it contains non-secret placeholders only and remains disabled.

## Issuer and Audience Requirements

A future validator must:

1. require exact issuer match,
2. require configured audience match,
3. reject missing issuer,
4. reject missing audience,
5. reject extra trust sources not present in config,
6. reject disabled config before token validation,
7. reject incomplete config before token validation.

Issuer comparison must be string-exact after config loading. No issuer normalization should be performed at authorization time.

## JWKS Retrieval and Cache Policy

A future JWKS implementation must:

1. retrieve keys only from configured `jwks_uri`,
2. reject non-HTTPS JWKS URIs unless an explicit local-test override is present,
3. cache JWKS deterministically with a configured TTL,
4. avoid hidden global cache state,
5. expose cache source and timestamp in diagnostics,
6. fail closed on retrieval errors,
7. fail closed on malformed JWKS,
8. fail closed on missing matching `kid`,
9. fail closed if `kid` is missing and `require_kid = true`.

The first implementation should support fixture/local JWKS loading before network retrieval. Network retrieval should be a separate later gate.

## Accepted Algorithms

A future validator must:

1. require `alg` in JWT header,
2. reject `alg = none`,
3. reject algorithms not listed in `accepted_algorithms`,
4. reject algorithm/key-type mismatch,
5. reject tokens with missing or unsupported `typ` only if the chosen validation library exposes it deterministically,
6. record the algorithm in diagnostics.

Initial production candidate algorithm:

```text
RS256
```

Additional algorithms require explicit design review before enablement.

## Time Claim Policy

A future validator must validate:

- `exp`,
- `nbf` when present,
- `iat` when present and policy requires it.

Clock skew must be explicit and bounded:

```text
0 <= clock_skew_seconds <= 300
```

Default proposed skew:

```text
60 seconds
```

Failure reasons must distinguish:

- expired token,
- token not yet valid,
- issued-at time too far in the future,
- malformed time claim.

## Claim-to-Reviewer Mapping

A future validator must map validated claims to reviewer identity only after all token validation succeeds.

Mapping requirements:

1. reviewer ID claim must be present and non-empty,
2. display name claim may fall back to reviewer ID,
3. email/username claim may fall back to reviewer ID,
4. groups/roles claims must be normalized to lists of strings,
5. required groups must be enforced if configured,
6. reviewer status and action authorization must remain policy controlled.

The validator must not infer reviewer privileges solely from token presence.

## Security-Denial Audit Integration

A future OIDC endpoint integration must write security-denial audit events for failures before mutation.

Denial reasons must use Gate 17C format:

```text
OIDC_DENIAL:<CATEGORY>:<AUDIT_SAFE_MESSAGE>
```

Future failure categories should include:

```text
CONFIG_DISABLED
CONFIG_INVALID
TOKEN_MISSING
TOKEN_MALFORMED_AUTHORIZATION_HEADER
TOKEN_EMPTY
TOKEN_MALFORMED_JWT
TOKEN_UNSAFE_PARSE_FAILED
TOKEN_VALIDATION_NOT_IMPLEMENTED
TOKEN_SIGNATURE_INVALID
TOKEN_KID_MISSING
TOKEN_KEY_NOT_FOUND
TOKEN_ALGORITHM_REJECTED
TOKEN_ISSUER_INVALID
TOKEN_AUDIENCE_INVALID
TOKEN_EXPIRED
TOKEN_NOT_YET_VALID
TOKEN_TIME_CLAIM_INVALID
REVIEWER_MAPPING_FAILED
REQUIRED_GROUP_MISSING
ACTION_NOT_ALLOWED
```

The security-denial audit schema should remain unchanged unless a future gate explicitly justifies schema migration.

## Endpoint Integration Guardrails

A future endpoint integration must:

1. be disabled by default,
2. preserve `LocalPolicyAuthAdapter` as the default adapter,
3. require explicit adapter selection,
4. preserve request provenance requirements,
5. deny before mutation,
6. write security-denial audit events for OIDC failures,
7. preserve review mutation audit for authorized mutations,
8. keep finalization disabled.

No endpoint integration should occur until a validation implementation and smoke harness both pass.

## Minimum Test Matrix for Implementation Gate

A future implementation gate must test:

### Config

- missing config fails closed,
- disabled config fails closed,
- incomplete enabled config fails closed,
- invalid JWKS URI fails closed,
- unsupported algorithm config fails closed.

### Bearer Header

- missing Authorization header,
- malformed scheme,
- empty bearer token,
- extra header segments.

### JWT Shape

- malformed segment count,
- invalid base64url,
- non-object header,
- non-object payload.

### Signature and Key

- missing `kid`,
- unknown `kid`,
- malformed key,
- invalid signature,
- valid fixture signature.

### Claims

- issuer mismatch,
- audience mismatch,
- expired token,
- not-yet-valid token,
- missing reviewer claim,
- missing required group,
- valid fixture reviewer mapping.

### Audit

- every denial writes an audit event,
- audit event uses mapped OIDC denial reason,
- audit hash chain validates,
- no review mutation occurs on denial.

## Recommended Implementation Sequence

After Gate 17E, proceed in small gates:

1. Gate 17F — Local JWKS Fixture Validation Helper.
2. Gate 17G — Deterministic JWT Signature Validation Against Fixture JWKS.
3. Gate 17H — Claim Validation and Reviewer Mapping Against Fixture Token.
4. Gate 17I — Disabled Endpoint OIDC Adapter Selection Smoke.
5. Gate 17J — Explicitly Configured OIDC Endpoint Integration.

Each gate must remain fail-closed and must preserve local-policy auth as the default until an explicit production enablement gate.

## Completion Criteria for Gate 17E

Gate 17E is complete when:

- this design spec is committed,
- the spec explicitly forbids token acceptance in Gate 17E,
- the spec defines issuer/audience/JWKS/algorithm/time-claim requirements,
- the spec defines reviewer mapping requirements,
- the spec defines audit integration requirements,
- the spec defines a minimum implementation test matrix,
- the spec recommends a bounded next implementation sequence.
