from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.scripts.apply_kb_review_update import read_json, regenerate_outputs, validate_state, write_json
from app.scripts.review_authorization import (
    RequestProvenance,
    append_provenance_to_latest_audit_event,
    authorize_reviewer,
    read_policy,
)
from app.scripts.review_update_service import ReviewUpdateRequest, ReviewUpdateResponse, apply_review_update_request


@dataclass(frozen=True)
class GuardedReviewUpdateResponse:
    status: str
    authorization_status: str
    reviewer_role: str
    request_id: str
    service_response: ReviewUpdateResponse


def apply_guarded_review_update_request(
    request: ReviewUpdateRequest,
    *,
    provenance: RequestProvenance,
    policy_path: Path | None = None,
    manifest_path: Path | None = None,
    output_path: Path | None = None,
    export_path: Path | None = None,
    surface_path: Path | None = None,
) -> GuardedReviewUpdateResponse:
    from app.scripts.extract_kb_source_manifest import repo_root

    root = repo_root()
    manifest_path = manifest_path or root / "kbs" / "review" / "kb_draft_review_manifest.v1.json"
    output_path = output_path or manifest_path
    export_path = export_path or root / "kbs" / "manifests" / "kb_draft_review_export.md"
    surface_path = surface_path or root / "kbs" / "manifests" / "kb_draft_review_surface.html"

    policy = read_policy(policy_path)
    authorized = authorize_reviewer(policy, reviewer_id=request.reviewer, action=request.action)
    service_response = apply_review_update_request(
        request,
        manifest_path=manifest_path,
        output_path=output_path,
        export_path=export_path,
        surface_path=surface_path,
    )

    manifest = read_json(output_path)
    append_provenance_to_latest_audit_event(
        manifest,
        authorized_reviewer=authorized,
        provenance=provenance,
    )
    write_json(output_path, manifest)
    validate_state(output_path)
    regenerate_outputs(output_path, export_path=export_path, surface_path=surface_path)
    manifest = read_json(output_path)

    service_response = ReviewUpdateResponse(
        status=service_response.status,
        action=service_response.action,
        target_id=service_response.target_id,
        reviewer=service_response.reviewer,
        manifest_path=service_response.manifest_path,
        export_path=service_response.export_path,
        surface_path=service_response.surface_path,
        review_status=str(manifest.get("review_status")),
        diagnostics=manifest.get("diagnostics") or {},
        audit_event_count=len(manifest.get("review_audit_events") or []),
        messages=[
            *service_response.messages,
            "Reviewer authorization was checked before mutation.",
            "Request provenance was appended to the latest audit event.",
        ],
    )

    return GuardedReviewUpdateResponse(
        status="OK",
        authorization_status="AUTHORIZED",
        reviewer_role=authorized.role,
        request_id=provenance.request_id,
        service_response=service_response,
    )


def guarded_response_to_dict(response: GuardedReviewUpdateResponse) -> dict[str, Any]:
    return asdict(response)
