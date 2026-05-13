from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


@dataclass(frozen=True)
class AuthorizedReviewer:
    reviewer_id: str
    role: str
    display_name: str


@dataclass(frozen=True)
class RequestProvenance:
    request_id: str
    route: str
    source: str
    user_agent: str
    remote_addr: str


def read_policy(path: Path | None = None) -> dict[str, Any]:
    root = repo_root()
    policy_path = path or root / "kbs" / "policies" / "review_authorization_policy.v1.json"
    if not policy_path.exists():
        raise FileNotFoundError(f"Review authorization policy not found: {policy_path}")
    return json.loads(policy_path.read_text(encoding="utf-8"))


def authorize_reviewer(policy: dict[str, Any], *, reviewer_id: str, action: str) -> AuthorizedReviewer:
    if policy.get("artifact_type") != "review_authorization_policy":
        raise ValueError("Invalid review authorization policy artifact_type.")
    if policy.get("schema_version") != "review_authorization_policy.v1":
        raise ValueError("Invalid review authorization policy schema_version.")
    if policy.get("finalization_allowed") is not False:
        raise ValueError("Review authorization policy must keep finalization disabled.")

    reviewer = next((item for item in policy.get("reviewers", []) if item.get("reviewer_id") == reviewer_id), None)
    if reviewer is None:
        raise PermissionError(f"Reviewer is not listed in authorization policy: {reviewer_id}")
    if reviewer.get("status") != "ACTIVE":
        raise PermissionError(f"Reviewer is not active: {reviewer_id}")
    role = reviewer.get("role")
    role_policy = (policy.get("roles") or {}).get(role)
    if role_policy is None:
        raise PermissionError(f"Reviewer role is not defined in policy: {role}")
    if action not in set(role_policy.get("allowed_actions") or []):
        raise PermissionError(f"Reviewer {reviewer_id} with role {role} is not allowed to perform action: {action}")
    if role_policy.get("can_finalize") is not False:
        raise PermissionError(f"Role {role} unexpectedly allows finalization.")
    return AuthorizedReviewer(
        reviewer_id=reviewer_id,
        role=str(role),
        display_name=str(reviewer.get("display_name") or reviewer_id),
    )


def append_provenance_to_latest_audit_event(
    manifest: dict[str, Any],
    *,
    authorized_reviewer: AuthorizedReviewer,
    provenance: RequestProvenance,
) -> None:
    events = manifest.get("review_audit_events") or []
    if not events:
        raise ValueError("Cannot append provenance because no audit events exist.")
    latest = events[-1]
    latest["request_provenance"] = {
        "request_id": provenance.request_id,
        "route": provenance.route,
        "source": provenance.source,
        "user_agent": provenance.user_agent,
        "remote_addr": provenance.remote_addr,
        "reviewer_role": authorized_reviewer.role,
        "reviewer_display_name": authorized_reviewer.display_name,
    }
    diagnostics = manifest.setdefault("diagnostics", {})
    diagnostics["provenance_audit_events"] = sum(1 for event in events if event.get("request_provenance"))


def provenance_from_headers(
    *,
    request_id: str,
    route: str,
    source: str,
    user_agent: str,
    remote_addr: str,
) -> RequestProvenance:
    if not request_id:
        raise ValueError("Request provenance requires a request_id.")
    return RequestProvenance(
        request_id=request_id,
        route=route,
        source=source or "UNKNOWN_SOURCE",
        user_agent=user_agent or "UNKNOWN_USER_AGENT",
        remote_addr=remote_addr or "UNKNOWN_REMOTE_ADDR",
    )
