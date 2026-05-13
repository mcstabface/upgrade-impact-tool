from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from app.scripts.auth_adapter import AuthenticatedPrincipal, ReviewerIdentity


@dataclass(frozen=True)
class FixtureClaimValidationFailure:
    code: str
    detail: str


@dataclass(frozen=True)
class FixtureClaimMappingResult:
    status: str
    principal: AuthenticatedPrincipal | None = None
    reviewer: ReviewerIdentity | None = None
    failures: list[FixtureClaimValidationFailure] = field(default_factory=list)
    authorization_allowed: bool = False


def _as_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value] if value.strip() else []
    if isinstance(value, list):
        return [str(item) for item in value if str(item).strip()]
    return []


def _now_timestamp(now_utc: datetime | None) -> int:
    selected = now_utc or datetime.now(timezone.utc)
    if selected.tzinfo is None:
        selected = selected.replace(tzinfo=timezone.utc)
    return int(selected.timestamp())


def validate_fixture_claims_and_map_reviewer(
    claims: dict[str, Any],
    *,
    expected_issuer: str,
    expected_audience: str,
    required_groups: list[str] | None = None,
    reviewer_id_claim: str = "preferred_username",
    display_name_claim: str = "name",
    email_claim: str = "email",
    groups_claim: str = "groups",
    role_claim: str = "roles",
    now_utc: datetime | None = None,
    clock_skew_seconds: int = 60,
) -> FixtureClaimMappingResult:
    failures: list[FixtureClaimValidationFailure] = []

    issuer = str(claims.get("iss") or "").strip()
    if issuer != expected_issuer:
        failures.append(FixtureClaimValidationFailure("JWT_ISSUER_INVALID", "Fixture issuer does not match expected issuer."))

    audience_value = claims.get("aud")
    audiences = _as_string_list(audience_value)
    if expected_audience not in audiences:
        failures.append(FixtureClaimValidationFailure("JWT_AUDIENCE_INVALID", "Fixture audience does not include expected audience."))

    now_ts = _now_timestamp(now_utc)
    skew = max(0, min(clock_skew_seconds, 300))
    exp = claims.get("exp")
    if exp is not None:
        try:
            if int(exp) < now_ts - skew:
                failures.append(FixtureClaimValidationFailure("JWT_EXPIRED", "Fixture token is expired."))
        except Exception:
            failures.append(FixtureClaimValidationFailure("JWT_TIME_CLAIM_INVALID", "Fixture exp claim is invalid."))
    nbf = claims.get("nbf")
    if nbf is not None:
        try:
            if int(nbf) > now_ts + skew:
                failures.append(FixtureClaimValidationFailure("JWT_NOT_YET_VALID", "Fixture token is not yet valid."))
        except Exception:
            failures.append(FixtureClaimValidationFailure("JWT_TIME_CLAIM_INVALID", "Fixture nbf claim is invalid."))

    reviewer_id = str(claims.get(reviewer_id_claim) or "").strip()
    if not reviewer_id:
        failures.append(FixtureClaimValidationFailure("REVIEWER_MAPPING_FAILED", "Fixture reviewer id claim is missing."))

    groups = _as_string_list(claims.get(groups_claim))
    roles = _as_string_list(claims.get(role_claim))
    required = required_groups or []
    missing_groups = [group for group in required if group not in groups]
    if missing_groups:
        failures.append(FixtureClaimValidationFailure("REQUIRED_GROUP_MISSING", "Fixture token is missing a required group."))

    if failures:
        return FixtureClaimMappingResult(status="ERROR", failures=failures, authorization_allowed=False)

    display_name = str(claims.get(display_name_claim) or reviewer_id).strip()
    email_or_username = str(claims.get(email_claim) or reviewer_id).strip()
    expires_at_utc = None
    if exp is not None:
        expires_at_utc = datetime.fromtimestamp(int(exp), tz=timezone.utc).isoformat()

    raw_claims = {key: str(value) for key, value in claims.items() if isinstance(key, str)}
    principal = AuthenticatedPrincipal(
        subject=reviewer_id,
        issuer=issuer,
        display_name=display_name,
        email_or_username=email_or_username,
        auth_method="oidc-fixture",
        expires_at_utc=expires_at_utc,
        groups=groups,
        raw_claims=raw_claims,
    )
    reviewer = ReviewerIdentity(
        reviewer_id=reviewer_id,
        principal_subject=principal.subject,
        principal_issuer=principal.issuer,
        reviewer_display_name=display_name,
        reviewer_email_or_username=email_or_username,
        roles=roles,
        status="fixture_validated",
    )
    return FixtureClaimMappingResult(status="OK", principal=principal, reviewer=reviewer, authorization_allowed=False)
