from __future__ import annotations

from pathlib import Path

from app.scripts.auth_adapter import AuthenticatedPrincipal, AuthorizationDecision, ReviewerIdentity
from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.review_authorization import read_policy


class LocalPolicyAuthAdapter:
    """Local-development adapter that maps reviewer IDs from request context to policy reviewers.

    This adapter is intentionally not production authentication. It exists to exercise the
    principal -> reviewer -> authorization interface using the Gate 15 local policy artifact.
    """

    def __init__(self, policy_path: Path | None = None) -> None:
        root = repo_root()
        self.policy_path = policy_path or root / "kbs" / "policies" / "review_authorization_policy.v1.json"
        self.policy = read_policy(self.policy_path)

    def get_authenticated_principal(self, request_context: dict[str, str]) -> AuthenticatedPrincipal:
        reviewer_id = request_context.get("reviewer_id", "").strip()
        if not reviewer_id:
            raise PermissionError("Local policy adapter requires reviewer_id in request context.")
        reviewer = next((item for item in self.policy.get("reviewers", []) if item.get("reviewer_id") == reviewer_id), None)
        if reviewer is None:
            raise PermissionError(f"Reviewer is not listed in local policy: {reviewer_id}")
        return AuthenticatedPrincipal(
            subject=reviewer_id,
            issuer="local-policy",
            display_name=str(reviewer.get("display_name") or reviewer_id),
            email_or_username=reviewer_id,
            auth_method="local_policy_smoke",
            groups=[str(reviewer.get("role"))],
            raw_claims={"reviewer_id": reviewer_id, "role": str(reviewer.get("role"))},
        )

    def map_principal_to_reviewer(self, principal: AuthenticatedPrincipal) -> ReviewerIdentity:
        reviewer = next((item for item in self.policy.get("reviewers", []) if item.get("reviewer_id") == principal.subject), None)
        if reviewer is None:
            raise PermissionError(f"Principal does not map to local reviewer: {principal.subject}")
        role = str(reviewer.get("role"))
        return ReviewerIdentity(
            reviewer_id=str(reviewer.get("reviewer_id")),
            principal_subject=principal.subject,
            principal_issuer=principal.issuer,
            reviewer_display_name=str(reviewer.get("display_name") or principal.display_name),
            reviewer_email_or_username=principal.email_or_username,
            roles=[role],
            status=str(reviewer.get("status")),
        )

    def authorize_action(self, reviewer: ReviewerIdentity, action: str) -> AuthorizationDecision:
        if reviewer.status != "ACTIVE":
            return AuthorizationDecision(False, f"Reviewer is not active: {reviewer.reviewer_id}", reviewer)
        roles = self.policy.get("roles") or {}
        for role in reviewer.roles:
            role_policy = roles.get(role) or {}
            if role_policy.get("can_finalize") is not False:
                return AuthorizationDecision(False, f"Role unexpectedly allows finalization: {role}", reviewer, role)
            if action in set(role_policy.get("allowed_actions") or []):
                return AuthorizationDecision(True, "Action allowed by local policy role.", reviewer, role)
        return AuthorizationDecision(False, f"No reviewer role allows action: {action}", reviewer)

    def authorize_request_context(self, request_context: dict[str, str], *, action: str) -> AuthorizationDecision:
        principal = self.get_authenticated_principal(request_context)
        reviewer = self.map_principal_to_reviewer(principal)
        return self.authorize_action(reviewer, action)
