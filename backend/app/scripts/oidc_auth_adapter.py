from __future__ import annotations

import base64
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Literal

from app.scripts.auth_adapter import AuthenticatedPrincipal, AuthorizationDecision, ReviewerIdentity
from app.scripts.extract_kb_source_manifest import repo_root


REQUIRED_ENABLED_FIELDS = ("issuer", "audience", "jwks_uri")
OIDCDiagnosticStatus = Literal["OK", "ERROR"]


@dataclass(frozen=True)
class OIDCAuthConfig:
    """Configuration contract for the future production OIDC auth adapter.

    Gate 17A intentionally adds the shape of the adapter without enabling token
    validation. This lets later gates wire production auth behind the AuthAdapter
    protocol without changing the guarded endpoint contract.
    """

    enabled: bool = False
    issuer: str = ""
    audience: str = ""
    jwks_uri: str = ""
    reviewer_id_claim: str = "preferred_username"
    display_name_claim: str = "name"
    email_claim: str = "email"
    groups_claim: str = "groups"
    role_claim: str = "roles"
    required_groups: list[str] = field(default_factory=list)
    config_source: str = "default-disabled"

    @classmethod
    def from_json(cls, payload: dict[str, Any], *, config_source: str) -> "OIDCAuthConfig":
        if not isinstance(payload, dict):
            raise ValueError("OIDC auth config must be a JSON object.")
        raw_required_groups = payload.get("required_groups") or []
        if not isinstance(raw_required_groups, list) or not all(isinstance(item, str) for item in raw_required_groups):
            raise ValueError("OIDC auth config required_groups must be a list of strings.")
        return cls(
            enabled=bool(payload.get("enabled", False)),
            issuer=str(payload.get("issuer") or ""),
            audience=str(payload.get("audience") or ""),
            jwks_uri=str(payload.get("jwks_uri") or ""),
            reviewer_id_claim=str(payload.get("reviewer_id_claim") or "preferred_username"),
            display_name_claim=str(payload.get("display_name_claim") or "name"),
            email_claim=str(payload.get("email_claim") or "email"),
            groups_claim=str(payload.get("groups_claim") or "groups"),
            role_claim=str(payload.get("role_claim") or "roles"),
            required_groups=list(raw_required_groups),
            config_source=config_source,
        )

    def validation_errors(self) -> list[str]:
        errors: list[str] = []
        if not self.enabled:
            return errors
        for field_name in REQUIRED_ENABLED_FIELDS:
            if not str(getattr(self, field_name)).strip():
                errors.append(f"enabled OIDC config requires {field_name}")
        for claim_field in ("reviewer_id_claim", "display_name_claim", "email_claim", "groups_claim", "role_claim"):
            if not str(getattr(self, claim_field)).strip():
                errors.append(f"OIDC config requires non-empty {claim_field}")
        return errors


def load_oidc_auth_config(config_path: Path | None = None) -> OIDCAuthConfig:
    root = repo_root()
    path = config_path or root / "kbs" / "policies" / "review_oidc_adapter.config.json"
    if not path.exists():
        return OIDCAuthConfig(config_source=f"missing:{path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return OIDCAuthConfig.from_json(payload, config_source=str(path))


@dataclass(frozen=True)
class BearerTokenExtraction:
    status: OIDCDiagnosticStatus
    token: str = ""
    failure_code: str = ""
    failure_reason: str = ""


@dataclass(frozen=True)
class UnsafeJWTDiagnostic:
    status: OIDCDiagnosticStatus
    header: dict[str, Any] = field(default_factory=dict)
    payload: dict[str, Any] = field(default_factory=dict)
    failure_code: str = ""
    failure_reason: str = ""
    authorization_allowed: bool = False


@dataclass(frozen=True)
class OIDCConfigDiagnostic:
    status: OIDCDiagnosticStatus
    enabled: bool
    config_source: str
    errors: list[str]
    required_fields: list[str]
    authorization_allowed: bool = False


def extract_bearer_token(request_context: dict[str, str]) -> BearerTokenExtraction:
    """Extract a bearer token deterministically without validating or accepting it."""
    authorization = (request_context.get("Authorization") or request_context.get("authorization") or "").strip()
    if not authorization:
        return BearerTokenExtraction("ERROR", failure_code="OIDC_TOKEN_MISSING", failure_reason="Authorization header is required.")
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return BearerTokenExtraction(
            "ERROR",
            failure_code="OIDC_TOKEN_MALFORMED_AUTHORIZATION_HEADER",
            failure_reason="Authorization header must use the form: Bearer <token>.",
        )
    token = parts[1].strip()
    if not token:
        return BearerTokenExtraction("ERROR", failure_code="OIDC_TOKEN_EMPTY", failure_reason="Bearer token is empty.")
    return BearerTokenExtraction("OK", token=token)


def _decode_base64url_json(segment: str) -> dict[str, Any]:
    padded = segment + "=" * (-len(segment) % 4)
    decoded = base64.urlsafe_b64decode(padded.encode("ascii"))
    payload = json.loads(decoded.decode("utf-8"))
    if not isinstance(payload, dict):
        raise ValueError("JWT segment must decode to a JSON object.")
    return payload


def unsafe_parse_jwt_without_verification(token: str) -> UnsafeJWTDiagnostic:
    """Parse JWT header/payload for diagnostics only.

    This helper deliberately does not validate signatures, issuer, audience, or
    time claims. Its result must never authorize a request.
    """
    parts = token.split(".")
    if len(parts) != 3:
        return UnsafeJWTDiagnostic(
            "ERROR",
            failure_code="OIDC_TOKEN_MALFORMED_JWT",
            failure_reason="JWT must contain exactly three dot-separated segments.",
        )
    try:
        header = _decode_base64url_json(parts[0])
        payload = _decode_base64url_json(parts[1])
    except Exception as exc:
        return UnsafeJWTDiagnostic(
            "ERROR",
            failure_code="OIDC_TOKEN_UNSAFE_PARSE_FAILED",
            failure_reason=str(exc),
        )
    return UnsafeJWTDiagnostic("OK", header=header, payload=payload, authorization_allowed=False)


def validate_oidc_config_for_diagnostics(config: OIDCAuthConfig) -> OIDCConfigDiagnostic:
    errors = config.validation_errors()
    status: OIDCDiagnosticStatus = "ERROR" if errors or not config.enabled else "OK"
    if not config.enabled:
        errors = [f"OIDC adapter disabled or missing config: {config.config_source}"]
    return OIDCConfigDiagnostic(
        status=status,
        enabled=config.enabled,
        config_source=config.config_source,
        errors=errors,
        required_fields=list(REQUIRED_ENABLED_FIELDS),
        authorization_allowed=False,
    )


class OIDCAuthAdapter:
    """Fail-closed OIDC auth adapter skeleton.

    This class implements the AuthAdapter protocol shape but intentionally does
    not validate tokens in Gate 17A/17B. Every runtime auth method fails closed
    until a later gate adds deterministic issuer/audience/JWKS validation.
    """

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = config_path
        self.config = load_oidc_auth_config(config_path)

    def _fail_closed_reason(self) -> str:
        errors = self.config.validation_errors()
        if not self.config.enabled:
            return f"OIDC auth adapter is disabled or missing config: {self.config.config_source}"
        if errors:
            return "OIDC auth adapter config is invalid: " + "; ".join(errors)
        return "OIDC auth adapter skeleton is not enabled for token validation in Gate 17B."

    def get_authenticated_principal(self, request_context: dict[str, str]) -> AuthenticatedPrincipal:
        _ = request_context
        raise PermissionError(self._fail_closed_reason())

    def map_principal_to_reviewer(self, principal: AuthenticatedPrincipal) -> ReviewerIdentity:
        _ = principal
        raise PermissionError("OIDC principal-to-reviewer mapping is not implemented in Gate 17B skeleton.")

    def authorize_action(self, reviewer: ReviewerIdentity, action: str) -> AuthorizationDecision:
        return AuthorizationDecision(
            allowed=False,
            reason=f"OIDC action authorization is not implemented in Gate 17B skeleton for action: {action}",
            reviewer_identity=reviewer,
        )

    def authorize_request_context(self, request_context: dict[str, str], *, action: str) -> AuthorizationDecision:
        _ = action
        try:
            principal = self.get_authenticated_principal(request_context)
            reviewer = self.map_principal_to_reviewer(principal)
            return self.authorize_action(reviewer, action)
        except PermissionError as exc:
            return AuthorizationDecision(False, str(exc), None, None)
