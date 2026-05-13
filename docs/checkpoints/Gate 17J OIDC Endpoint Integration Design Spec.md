# Gate 17J OIDC Endpoint Integration Design Spec

System: Upgrade Impact Analysis Tool  
Phase: Explicitly Configured OIDC Endpoint Integration Design  
Status: Proposed design  
Generated: 2026-05-13

## Purpose

Gate 17J defines how OIDC could later be integrated into the guarded review endpoint without changing the default local-policy path.

This gate is design-only. It does not change the live endpoint, does not enable OIDC, does not accept production tokens, and does not enable finalization.

## Baseline

Gate 17J starts after Gate 17I:

- local-policy auth remains the live guarded endpoint default,
- disabled OIDC adapter selection smoke exists,
- fixture signature and claim mapping helpers exist,
- OIDC denial reasons map into security-denial audit events,
- finalization remains disabled.

## Required Integration Rule

A future endpoint integration must require explicit adapter selection. Silent fallback to OIDC is forbidden.

Proposed config:

```json
{
  "review_update_auth_adapter": "local_policy",
  "allow_oidc_adapter": false,
  "oidc_config_path": "kbs/policies/review_oidc_adapter.config.json",
  "local_policy_path": "kbs/policies/review_authorization_policy.v1.json"
}
```

Allowed adapter values:

```text
local_policy
oidc
```

Default must remain:

```text
local_policy
```

## OIDC Enablement Guardrails

OIDC may be selected only when all are true:

1. endpoint adapter config selects `oidc`,
2. `allow_oidc_adapter = true`,
3. OIDC adapter config exists,
4. OIDC adapter config is enabled,
5. OIDC token validation implementation exists,
6. denial audit mapping is active,
7. request provenance validation remains active.

If any condition fails, the endpoint must deny before mutation and write a security-denial audit event.

## Fail-Closed Requirements

A future endpoint integration must fail closed for:

- missing adapter config,
- unknown adapter name,
- OIDC selected while `allow_oidc_adapter = false`,
- missing OIDC config,
- disabled OIDC config,
- invalid OIDC config,
- missing bearer token,
- malformed bearer token,
- invalid signature,
- invalid issuer,
- invalid audience,
- invalid time claims,
- reviewer mapping failure,
- missing required group,
- action not allowed.

## Audit Requirements

Every OIDC denial before mutation must write a security-denial audit event with:

```text
route = /review/update
source = guarded-review-update-endpoint
principal_issuer = oidc
finalization_allowed = false
denial_reason = OIDC_DENIAL:<CATEGORY>:<MESSAGE>
```

The existing security-denial audit schema should remain unchanged.

## Provenance Requirements

Request provenance must remain mandatory regardless of adapter selection.

The endpoint must reject missing request ID before mutation. OIDC integration must not relax Gate 15 provenance rules.

## Mutation Requirements

Authorized review mutation must remain behind the existing review update service contract.

OIDC integration must not bypass:

- review update request validation,
- mutation audit,
- artifact regeneration,
- finalization-disabled controls.

## Rollback Requirements

Rollback must be simple:

```json
{
  "review_update_auth_adapter": "local_policy",
  "allow_oidc_adapter": false
}
```

Rollback must not require code deletion.

## Required Test Matrix Before Implementation

A future implementation gate must test:

- default config uses local-policy adapter,
- unknown adapter name denies,
- OIDC selected but not allowed denies,
- OIDC selected with missing config denies,
- OIDC selected with disabled config denies,
- OIDC selected with invalid token denies,
- OIDC denial writes security-denial audit event,
- missing provenance still rejects before mutation,
- local-policy authorized mutation still succeeds,
- finalization remains disabled.

## Recommended Next Gate

Recommended next gate:

**Gate 17K — Endpoint Adapter Selection Config Skeleton**

Gate 17K should add config loading and validation for adapter selection only. It should keep the endpoint default on local policy and should not enable OIDC.