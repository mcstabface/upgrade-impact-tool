from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root

ALLOWED_DECISIONS = {"ACCEPT", "REJECT", "NEEDS_MORE_EVIDENCE", "UNSET"}


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


def update_claim_decision(
    manifest: dict[str, Any],
    *,
    claim_id: str,
    decision: str,
    reviewer: str,
    notes: str,
    visual_acknowledged: bool,
) -> dict[str, Any]:
    if decision not in ALLOWED_DECISIONS:
        raise ValueError(f"Unsupported decision {decision!r}. Expected one of {sorted(ALLOWED_DECISIONS)}.")

    tasks = manifest.get("claim_review_tasks") or []
    for task in tasks:
        if task.get("claim_id") != claim_id:
            continue
        if decision == "ACCEPT" and task.get("requires_visual_review") and not visual_acknowledged:
            raise ValueError(
                f"Claim {claim_id} cites image-bearing evidence and cannot be accepted without --visual-acknowledged."
            )
        task["reviewer_decision"] = decision
        task["review_status"] = "PENDING_REVIEW" if decision == "UNSET" else "REVIEWED"
        task["reviewer"] = reviewer
        task["reviewer_notes"] = notes
        task["visual_acknowledgement_status"] = "ACKNOWLEDGED" if visual_acknowledged else "UNSET"
        task["updated_utc"] = datetime.now(timezone.utc).isoformat()
        recompute_diagnostics(manifest)
        manifest["review_status"] = "IN_REVIEW"
        return manifest

    raise KeyError(f"Claim review task not found: {claim_id}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Update one Gate 10 KB draft claim review decision.")
    parser.add_argument("claim_id", help="Claim ID to update.")
    parser.add_argument("decision", choices=sorted(ALLOWED_DECISIONS), help="Reviewer decision.")
    parser.add_argument("--manifest", type=Path, default=root / "kbs" / "review" / "kb_draft_review_manifest.v1.json")
    parser.add_argument("--output", type=Path, help="Output path. Defaults to overwriting --manifest.")
    parser.add_argument("--reviewer", default="UNSPECIFIED_REVIEWER", help="Reviewer identifier.")
    parser.add_argument("--notes", default="", help="Reviewer notes.")
    parser.add_argument("--visual-acknowledged", action="store_true", help="Acknowledge required visual review for image-bearing evidence.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output or args.manifest
    manifest = read_json(args.manifest)
    updated = update_claim_decision(
        manifest,
        claim_id=args.claim_id,
        decision=args.decision,
        reviewer=args.reviewer,
        notes=args.notes,
        visual_acknowledged=args.visual_acknowledged,
    )
    write_json(output, updated)
    print(f"Updated claim decision: {args.claim_id} -> {args.decision}")
    print(f"Wrote review manifest: {output}")


if __name__ == "__main__":
    main()
