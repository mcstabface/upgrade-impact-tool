from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Literal

from app.scripts.apply_kb_review_update import (
    apply_claim_update,
    apply_gap_update,
    read_json,
    regenerate_outputs,
    validate_state,
    write_json,
)
from app.scripts.extract_kb_source_manifest import relpath, repo_root

ReviewAction = Literal["claim", "gap"]
ClaimDecision = Literal["ACCEPT", "REJECT", "NEEDS_MORE_EVIDENCE", "UNSET"]
GapAcknowledgement = Literal["ACKNOWLEDGED", "NEEDS_MORE_EVIDENCE", "UNSET"]


@dataclass(frozen=True)
class ReviewUpdateRequest:
    action: ReviewAction
    target_id: str
    value: str
    reviewer: str
    notes: str = ""
    visual_acknowledged: bool = False


@dataclass(frozen=True)
class ReviewUpdateResponse:
    status: str
    action: str
    target_id: str
    reviewer: str
    manifest_path: str
    export_path: str
    surface_path: str
    review_status: str
    diagnostics: dict[str, Any]
    audit_event_count: int
    messages: list[str] = field(default_factory=list)


def response_from_manifest(
    *,
    request: ReviewUpdateRequest,
    manifest: dict[str, Any],
    manifest_path: Path,
    export_path: Path,
    surface_path: Path,
    messages: list[str],
) -> ReviewUpdateResponse:
    root = repo_root()
    return ReviewUpdateResponse(
        status="OK",
        action=request.action,
        target_id=request.target_id,
        reviewer=request.reviewer,
        manifest_path=relpath(manifest_path, root),
        export_path=relpath(export_path, root),
        surface_path=relpath(surface_path, root),
        review_status=str(manifest.get("review_status")),
        diagnostics=manifest.get("diagnostics") or {},
        audit_event_count=len(manifest.get("review_audit_events") or []),
        messages=messages,
    )


def apply_review_update_request(
    request: ReviewUpdateRequest,
    *,
    manifest_path: Path | None = None,
    output_path: Path | None = None,
    export_path: Path | None = None,
    surface_path: Path | None = None,
) -> ReviewUpdateResponse:
    root = repo_root()
    manifest_path = manifest_path or root / "kbs" / "review" / "kb_draft_review_manifest.v1.json"
    output_path = output_path or manifest_path
    export_path = export_path or root / "kbs" / "manifests" / "kb_draft_review_export.md"
    surface_path = surface_path or root / "kbs" / "manifests" / "kb_draft_review_surface.html"

    if not request.reviewer.strip():
        raise ValueError("Reviewer is required for review update requests.")
    if not request.target_id.strip():
        raise ValueError("target_id is required for review update requests.")

    manifest = read_json(manifest_path)
    if request.action == "claim":
        if request.value not in {"ACCEPT", "REJECT", "NEEDS_MORE_EVIDENCE", "UNSET"}:
            raise ValueError(f"Unsupported claim decision: {request.value!r}")
        updated = apply_claim_update(
            manifest,
            claim_id=request.target_id,
            decision=request.value,
            reviewer=request.reviewer,
            notes=request.notes,
            visual_acknowledged=request.visual_acknowledged,
        )
    elif request.action == "gap":
        if request.value not in {"ACKNOWLEDGED", "NEEDS_MORE_EVIDENCE", "UNSET"}:
            raise ValueError(f"Unsupported gap acknowledgement: {request.value!r}")
        updated = apply_gap_update(
            manifest,
            gap_id=request.target_id,
            acknowledgement=request.value,
            reviewer=request.reviewer,
            notes=request.notes,
        )
    else:
        raise ValueError(f"Unsupported review update action: {request.action!r}")

    write_json(output_path, updated)
    validate_state(output_path)
    regenerate_outputs(output_path, export_path=export_path, surface_path=surface_path)
    final_manifest = read_json(output_path)
    return response_from_manifest(
        request=request,
        manifest=final_manifest,
        manifest_path=output_path,
        export_path=export_path,
        surface_path=surface_path,
        messages=[
            "Review update applied through Gate 12 bridge functions.",
            "Review state validated after mutation.",
            "Reviewer export and static surface regenerated after mutation.",
        ],
    )


def request_from_json(payload: dict[str, Any]) -> ReviewUpdateRequest:
    return ReviewUpdateRequest(
        action=payload.get("action"),
        target_id=str(payload.get("target_id") or ""),
        value=str(payload.get("value") or ""),
        reviewer=str(payload.get("reviewer") or ""),
        notes=str(payload.get("notes") or ""),
        visual_acknowledged=bool(payload.get("visual_acknowledged", False)),
    )


def response_to_json(response: ReviewUpdateResponse) -> str:
    return json.dumps(asdict(response), indent=2, sort_keys=True) + "\n"
