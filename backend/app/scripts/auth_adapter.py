from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol


@dataclass(frozen=True)
class AuthenticatedPrincipal:
    subject: str
    issuer: str
    display_name: str
    email_or_username: str
    auth_method: str
    expires_at_utc: str | None = None
    groups: list[str] = field(default_factory=list)
    raw_claims: dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class ReviewerIdentity:
    reviewer_id: str
    principal_subject: str
    principal_issuer: str
    reviewer_display_name: str
    reviewer_email_or_username: str
    roles: list[str]
    status: str


@dataclass(frozen=True)
class AuthorizationDecision:
    allowed: bool
    reason: str
    reviewer_identity: ReviewerIdentity | None = None
    role_used: str | None = None


class AuthAdapter(Protocol):
    def get_authenticated_principal(self, request_context: dict[str, str]) -> AuthenticatedPrincipal:
        """Extract and validate an authenticated principal from request context."""

    def map_principal_to_reviewer(self, principal: AuthenticatedPrincipal) -> ReviewerIdentity:
        """Map an authenticated principal to a reviewer identity and roles."""

    def authorize_action(self, reviewer: ReviewerIdentity, action: str) -> AuthorizationDecision:
        """Authorize a reviewer identity for a review action."""
