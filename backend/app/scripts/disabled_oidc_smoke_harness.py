from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.scripts.oidc_auth_adapter import (
    extract_bearer_token,
    load_oidc_auth_config,
    unsafe_parse_jwt_without_verification,
    validate_oidc_config_for_diagnostics,
)
from app.scripts.oidc_denial_reasons import map_oidc_failure_code_to_denial_reason
from app.scripts.security_denial_audit import SecurityDenialAuditEvent, append_security_denial_event


@dataclass(frozen=True)
class DisabledOIDCSmokeScenario:
    name: str
    request_context: dict[str, str]
    expected_failure_code: str


@dataclass(frozen=True)
class DisabledOIDCSmokeResult:
    name: str
    failure_code: str
    denial_reason: str
    audit_event_id: str
    authorization_allowed: bool = False


def default_disabled_oidc_smoke_scenarios() -> list[DisabledOIDCSmokeScenario]:
    return [
        DisabledOIDCSmokeScenario(
            name="missing_authorization_header",
            request_context={},
            expected_failure_code="OIDC_TOKEN_MISSING",
        ),
        DisabledOIDCSmokeScenario(
            name="malformed_authorization_header",
            request_context={"Authorization": "Basic abc123"},
            expected_failure_code="OIDC_TOKEN_MALFORMED_AUTHORIZATION_HEADER",
        ),
        DisabledOIDCSmokeScenario(
            name="malformed_jwt",
            request_context={"Authorization": "Bearer not-a-jwt"},
            expected_failure_code="OIDC_TOKEN_MALFORMED_JWT",
        ),
    ]


def diagnose_disabled_oidc_request(request_context: dict[str, str], *, config_path: Path | None = None) -> str:
    """Return an OIDC diagnostic failure code without authorizing the request."""
    config = load_oidc_auth_config(config_path)
    config_diagnostic = validate_oidc_config_for_diagnostics(config)
    if config_diagnostic.status == "ERROR" and not config.enabled:
        # In the disabled smoke harness, token formatting is still diagnosed first so
        # operator mistakes produce precise failure reasons. Disabled/missing config is
        # covered by the config validator and remains non-authorizing.
        pass

    bearer = extract_bearer_token(request_context)
    if bearer.status == "ERROR":
        return bearer.failure_code

    jwt_diagnostic = unsafe_parse_jwt_without_verification(bearer.token)
    if jwt_diagnostic.status == "ERROR":
        return jwt_diagnostic.failure_code

    return "OIDC_TOKEN_VALIDATION_NOT_IMPLEMENTED"


def run_disabled_oidc_smoke_harness(
    *,
    audit_path: Path,
    scenarios: list[DisabledOIDCSmokeScenario] | None = None,
    config_path: Path | None = None,
) -> list[DisabledOIDCSmokeResult]:
    selected_scenarios = scenarios or default_disabled_oidc_smoke_scenarios()
    results: list[DisabledOIDCSmokeResult] = []
    for index, scenario in enumerate(selected_scenarios, start=1):
        failure_code = diagnose_disabled_oidc_request(scenario.request_context, config_path=config_path)
        if failure_code != scenario.expected_failure_code:
            raise AssertionError(
                f"Scenario {scenario.name} expected {scenario.expected_failure_code}, got {failure_code}."
            )
        mapped = map_oidc_failure_code_to_denial_reason(failure_code)
        event: SecurityDenialAuditEvent = append_security_denial_event(
            audit_path=audit_path,
            request_id=f"gate17d-oidc-smoke-{index:04d}",
            route="/review/update",
            action="claim",
            target_id="evidence_group_006",
            reviewer_id="UNKNOWN_REVIEWER",
            principal_subject="UNKNOWN_PRINCIPAL",
            principal_issuer="oidc-disabled-smoke",
            denial_reason=mapped.denial_reason,
            source="gate17d-disabled-oidc-smoke",
            user_agent="gate17d-smoke-harness",
        )
        results.append(
            DisabledOIDCSmokeResult(
                name=scenario.name,
                failure_code=failure_code,
                denial_reason=mapped.denial_reason,
                audit_event_id=event.event_id,
                authorization_allowed=False,
            )
        )
    return results
