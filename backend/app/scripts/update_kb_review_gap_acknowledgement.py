from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root

ALLOWED_ACKNOWLEDGEMENTS = {"ACKNOWLEDGED", "NEEDS_MORE_EVIDENCE", "UNSET"}


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def recompute_diagnostics(manifest: dict[str, Any]) -> None:
    tasks = manifest.get("claim_review_tasks") or []
    gaps = manifest.get("unresolved_gap_tasks") or []
    manifest["diagnostics"] = {
        **(manifest.get("diagnostics") or {}),
        "claim_review_tasks": len(tasks),
        "evidence_review_tasks": sum(1 for task in tasks if task.get("requires_evidence_review")),
        "visual_review_tasks": sum(1 for task in tasks if task.get("requires_visual_review")),
        "unresolved_gap_tasks": len(gaps),
        "accepted_claims": sum(1 for task in tasks if task.get("reviewer_decision") == "ACCEPT"),
        "rejected_claims": sum(1 for task in tasks if task.get("reviewer_decision") == "REJECT"),
        "needs_more_evidence_claims": sum(1 for task in tasks if task.get("reviewer_decision") == "NEEDS_MORE_EVIDENCE"),
        "acknowledged_gaps": sum(1 for task in gaps if task.get("acknowledgement_status") == "ACKNOWLEDGED"),
    }


def update_gap_acknowledgement(
    manifest: dict[str, Any],
    *,
    gap_id: str,
    acknowledgement: str,
    reviewer: str,
    notes: str,
) -> dict[str, Any]:
    if acknowledgement not in ALLOWED_ACKNOWLEDGEMENTS:
        raise ValueError(
            f"Unsupported acknowledgement {acknowledgement!r}. Expected one of {sorted(ALLOWED_ACKNOWLEDGEMENTS)}."
        )

    for task in manifest.get("unresolved_gap_tasks") or []:
        if task.get("gap_id") != gap_id:
            continue
        task["acknowledgement_status"] = acknowledgement
        task["review_status"] = "PENDING_ACKNOWLEDGEMENT" if acknowledgement == "UNSET" else "ACKNOWLEDGED"
        task["reviewer"] = reviewer
        task["reviewer_notes"] = notes
        task["updated_utc"] = datetime.now(timezone.utc).isoformat()
        recompute_diagnostics(manifest)
        manifest["review_status"] = "IN_REVIEW"
        return manifest

    raise KeyError(f"Gap acknowledgement task not found: {gap_id}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Update one Gate 10 unresolved gap acknowledgement.")
    parser.add_argument("gap_id", help="Gap ID to update.")
    parser.add_argument("acknowledgement", choices=sorted(ALLOWED_ACKNOWLEDGEMENTS), help="Acknowledgement status.")
    parser.add_argument("--manifest", type=Path, default=root / "kbs" / "review" / "kb_draft_review_manifest.v1.json")
    parser.add_argument("--output", type=Path, help="Output path. Defaults to overwriting --manifest.")
    parser.add_argument("--reviewer", default="UNSPECIFIED_REVIEWER", help="Reviewer identifier.")
    parser.add_argument("--notes", default="", help="Reviewer notes.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output or args.manifest
    manifest = read_json(args.manifest)
    updated = update_gap_acknowledgement(
        manifest,
        gap_id=args.gap_id,
        acknowledgement=args.acknowledgement,
        reviewer=args.reviewer,
        notes=args.notes,
    )
    write_json(output, updated)
    print(f"Updated gap acknowledgement: {args.gap_id} -> {args.acknowledgement}")
    print(f"Wrote review manifest: {output}")


if __name__ == "__main__":
    main()
