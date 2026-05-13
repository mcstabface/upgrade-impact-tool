from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


ALLOWED_REVIEW_UPDATE_AUTH_ADAPTERS = ("local_policy", "oidc")
DEFAULT_REVIEW_UPDATE_AUTH_ADAPTER = "local_policy"


@dataclass(frozen=True)
class EndpointAdapterSelectionConfig:
    review_update_auth_adapter: str = DEFAULT_REVIEW_UPDATE_AUTH_ADAPTER
    allow_oidc_adapter: bool = False
    oidc_config_path: str = "kbs/policies/review_oidc_adapter.config.json"
    local_policy_path: str = "kbs/policies/review_authorization_policy.v1.json"
    config_source: str = "default-local-policy"

    @classmethod
    def from_json(cls, payload: dict[str, Any], *, config_source: str) -> "EndpointAdapterSelectionConfig":
        if not isinstance(payload, dict):
            raise ValueError("Endpoint adapter selection config must be a JSON object.")
        return cls(
            review_update_auth_adapter=str(payload.get("review_update_auth_adapter") or DEFAULT_REVIEW_UPDATE_AUTH_ADAPTER),
            allow_oidc_adapter=bool(payload.get("allow_oidc_adapter", False)),
            oidc_config_path=str(payload.get("oidc_config_path") or "kbs/policies/review_oidc_adapter.config.json"),
            local_policy_path=str(payload.get("local_policy_path") or "kbs/policies/review_authorization_policy.v1.json"),
            config_source=config_source,
        )

    def validation_errors(self) -> list[str]:
        errors: list[str] = []
        adapter = self.review_update_auth_adapter.strip()
        if adapter not in ALLOWED_REVIEW_UPDATE_AUTH_ADAPTERS:
            errors.append(f"unsupported review_update_auth_adapter: {adapter}")
        if adapter == "oidc" and not self.allow_oidc_adapter:
            errors.append("oidc adapter selected but allow_oidc_adapter is false")
        if not self.local_policy_path.strip():
            errors.append("local_policy_path is required")
        if adapter == "oidc" and not self.oidc_config_path.strip():
            errors.append("oidc_config_path is required when oidc adapter is selected")
        return errors

    @property
    def is_local_policy_default(self) -> bool:
        return self.review_update_auth_adapter == DEFAULT_REVIEW_UPDATE_AUTH_ADAPTER and self.allow_oidc_adapter is False


@dataclass(frozen=True)
class EndpointAdapterSelectionDiagnostic:
    status: str
    config: EndpointAdapterSelectionConfig
    errors: list[str] = field(default_factory=list)
    endpoint_integration_allowed: bool = False


def load_endpoint_adapter_selection_config(config_path: Path | None = None) -> EndpointAdapterSelectionConfig:
    root = repo_root()
    path = config_path or root / "kbs" / "policies" / "review_endpoint_auth_adapter.config.json"
    if not path.exists():
        return EndpointAdapterSelectionConfig(config_source=f"missing:{path}")
    payload = json.loads(path.read_text(encoding="utf-8"))
    return EndpointAdapterSelectionConfig.from_json(payload, config_source=str(path))


def validate_endpoint_adapter_selection_config(config: EndpointAdapterSelectionConfig) -> EndpointAdapterSelectionDiagnostic:
    errors = config.validation_errors()
    return EndpointAdapterSelectionDiagnostic(
        status="ERROR" if errors else "OK",
        config=config,
        errors=errors,
        endpoint_integration_allowed=False,
    )
