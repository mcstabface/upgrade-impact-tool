from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from app.scripts.apply_kb_review_update import read_json, write_json
from app.scripts.extract_kb_source_manifest import relpath, repo_root
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

    # Regenerate artifacts once more so reviewer-facing outputs reflect provenance-enhanced audit metadata if rendered later.
    service_response = apply_review_update_request(
        ReviewUpdateRequest(
            action=request.action,
            target_id=request.target_id,
            value=request.value,
            reviewer=request.reviewer,
            notes=request.notes,
            visual_acknowledged=request.visual_acknowledged,
        ),
        manifest_path=output_path,
        output_path=output_path,
        export_path=export_path,
        surface_path=surface_path,
    ) if False else service_response

    return GuardedReviewUpdateResponse(
        status="OK",
        authorization_status="AUTHORIZED",
        reviewer_role=authorized.role,
        request_id=provenance.request_id,
        service_response=service_response,
    )


def guarded_response_to_dict(response: GuardedReviewUpdateResponse) -> dict[str, Any]:
    payload = asdict(response)
    service_response = payload.get("service_response") or {}
    if service_response.get("manifest_path"):
        root = repo_root()
        service_response["manifest_path"] = relpath(root / service_response["manifest_path"], root)
    return payload
