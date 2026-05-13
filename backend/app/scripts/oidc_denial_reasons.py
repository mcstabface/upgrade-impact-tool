from __future__ import annotations

from dataclasses import dataclass
from typing import Final


OIDC_DENIAL_PREFIX: Final[str] = "OIDC_DENIAL"

OIDC_DENIAL_REASON_BY_CODE: Final[dict[str, str]] = {
    "OIDC_CONFIG_DISABLED": "OIDC_DENIAL:CONFIG_DISABLED:OIDC adapter is disabled or missing configuration.",
    "OIDC_CONFIG_INVALID": "OIDC_DENIAL:CONFIG_INVALID:OIDC adapter configuration is invalid.",
    "OIDC_TOKEN_MISSING": "OIDC_DENIAL:TOKEN_MISSING:Authorization bearer token is required.",
    "OIDC_TOKEN_MALFORMED_AUTHORIZATION_HEADER": "OIDC_DENIAL:TOKEN_MALFORMED_AUTHORIZATION_HEADER:Authorization header must use Bearer scheme.",
    "OIDC_TOKEN_EMPTY": "OIDC_DENIAL:TOKEN_EMPTY:Bearer token is empty.",
    "OIDC_TOKEN_MALFORMED_JWT": "OIDC_DENIAL:TOKEN_MALFORMED_JWT:Bearer token is not a three-segment JWT.",
    "OIDC_TOKEN_UNSAFE_PARSE_FAILED": "OIDC_DENIAL:TOKEN_UNSAFE_PARSE_FAILED:JWT diagnostic parse failed.",
    "OIDC_TOKEN_VALIDATION_NOT_IMPLEMENTED": "OIDC_DENIAL:TOKEN_VALIDATION_NOT_IMPLEMENTED:OIDC token validation is not implemented in this gate.",
    "OIDC_REVIEWER_MAPPING_NOT_IMPLEMENTED": "OIDC_DENIAL:REVIEWER_MAPPING_NOT_IMPLEMENTED:OIDC reviewer mapping is not implemented in this gate.",
    "OIDC_ACTION_AUTHORIZATION_NOT_IMPLEMENTED": "OIDC_DENIAL:ACTION_AUTHORIZATION_NOT_IMPLEMENTED:OIDC action authorization is not implemented in this gate.",
}


@dataclass(frozen=True)
class OIDCDenialReason:
    code: str
    denial_reason: str
    audit_safe: bool


def map_oidc_failure_code_to_denial_reason(code: str) -> OIDCDenialReason:
    normalized = code.strip().upper()
    if normalized in OIDC_DENIAL_REASON_BY_CODE:
        reason = OIDC_DENIAL_REASON_BY_CODE[normalized]
        return OIDCDenialReason(code=normalized, denial_reason=reason, audit_safe=True)
    return OIDCDenialReason(
        code="OIDC_UNKNOWN_FAILURE",
        denial_reason="OIDC_DENIAL:UNKNOWN_FAILURE:OIDC failure code is not recognized.",
        audit_safe=True,
    )


def is_audit_safe_oidc_denial_reason(reason: str) -> bool:
    if not reason.startswith(f"{OIDC_DENIAL_PREFIX}:"):
        return False
    if "\n" in reason or "\r" in reason or "\t" in reason:
        return False
    if len(reason) > 240:
        return False
    parts = reason.split(":")
    if len(parts) < 3:
        return False
    if parts[0] != OIDC_DENIAL_PREFIX:
        return False
    if not parts[1].replace("_", "").isalnum():
        return False
    return True


def oidc_denial_reason_catalog() -> list[OIDCDenialReason]:
    return [map_oidc_failure_code_to_denial_reason(code) for code in sorted(OIDC_DENIAL_REASON_BY_CODE)]
