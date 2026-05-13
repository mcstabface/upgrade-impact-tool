from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.scripts.auth_adapter import AuthorizationDecision
from app.scripts.local_policy_auth_adapter import LocalPolicyAuthAdapter
from app.scripts.oidc_auth_adapter import OIDCAuthAdapter
from app.scripts.oidc_denial_reasons import map_oidc_failure_code_to_denial_reason
from app.scripts.security_denial_audit import SecurityDenialAuditEvent, append_security_denial_event


@dataclass(frozen=True)
class AdapterSelectionSmokeResult:
    adapter_name: str
    selected: bool
    authorization_allowed: bool
    reason: str
    audit_event_id: str | None = None


def select_adapter_for_disabled_smoke(adapter_name: str, *, policy_path: Path | None = None, oidc_config_path: Path | None = None) -> object:
    selected = adapter_name.strip().lower()
    if selected == "local_policy":
        if policy_path is None:
            raise ValueError("policy_path is required for local_policy adapter selection smoke.")
        return LocalPolicyAuthAdapter(policy_path)
    if selected == "oidc_disabled":
        return OIDCAuthAdapter(oidc_config_path)
    raise ValueError(f"Unsupported adapter selection smoke adapter: {adapter_name}")


def run_disabled_oidc_adapter_selection_smoke(
    *,
    audit_path: Path,
    oidc_config_path: Path | None = None,
    request_context: dict[str, str] | None = None,
    action: str = "claim",
) -> AdapterSelectionSmokeResult:
    adapter = select_adapter_for_disabled_smoke("oidc_disabled", oidc_config_path=oidc_config_path)
    if not isinstance(adapter, OIDCAuthAdapter):
        raise AssertionError("Disabled OIDC smoke selected the wrong adapter type.")

    decision: AuthorizationDecision = adapter.authorize_request_context(request_context or {}, action=action)
    if decision.allowed:
        raise AssertionError("Disabled OIDC adapter selection smoke must not authorize.")

    mapped = map_oidc_failure_code_to_denial_reason("OIDC_CONFIG_DISABLED")
    event: SecurityDenialAuditEvent = append_security_denial_event(
        audit_path=audit_path,
        request_id="gate17i-disabled-adapter-selection-0001",
        route="/review/update",
        action=action,
        target_id="evidence_group_006",
        reviewer_id="UNKNOWN_REVIEWER",
        principal_subject="UNKNOWN_PRINCIPAL",
        principal_issuer="oidc-disabled-adapter-selection",
        denial_reason=mapped.denial_reason,
        source="gate17i-disabled-adapter-selection-smoke",
        user_agent="gate17i-smoke-harness",
    )
    return AdapterSelectionSmokeResult(
        adapter_name="oidc_disabled",
        selected=True,
        authorization_allowed=False,
        reason=decision.reason,
        audit_event_id=event.event_id,
    )
