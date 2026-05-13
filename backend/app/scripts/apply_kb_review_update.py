from __future__ import annotations

import argparse
import json
import subprocess
import sys
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.update_kb_review_claim_decision import update_claim_decision
from app.scripts.update_kb_review_gap_acknowledgement import update_gap_acknowledgement


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def find_claim_task(manifest: dict[str, Any], claim_id: str) -> dict[str, Any]:
    for task in manifest.get("claim_review_tasks") or []:
        if task.get("claim_id") == claim_id:
            return task
    raise KeyError(f"Claim review task not found: {claim_id}")


def find_gap_task(manifest: dict[str, Any], gap_id: str) -> dict[str, Any]:
    for task in manifest.get("unresolved_gap_tasks") or []:
        if task.get("gap_id") == gap_id:
            return task
    raise KeyError(f"Gap acknowledgement task not found: {gap_id}")


def append_audit_event(
    manifest: dict[str, Any],
    *,
    action_type: str,
    target_id: str,
    reviewer: str,
    previous_state: dict[str, Any],
    new_state: dict[str, Any],
) -> None:
    audit_events = manifest.setdefault("review_audit_events", [])
    audit_events.append(
        {
            "event_id": f"review_event_{len(audit_events) + 1:04d}",
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "action_type": action_type,
            "target_id": target_id,
            "reviewer": reviewer,
            "previous_state": previous_state,
            "new_state": new_state,
        }
    )
    diagnostics = manifest.setdefault("diagnostics", {})
    diagnostics["review_audit_events"] = len(audit_events)


def validate_state(manifest_path: Path) -> None:
    command = [sys.executable, "-m", "app.scripts.validate_kb_review_state", "--manifest", str(manifest_path)]
    subprocess.run(command, check=True)


def regenerate_outputs(manifest_path: Path, *, export_path: Path, surface_path: Path) -> None:
    subprocess.run(
        [
            sys.executable,
            "-m",
            "app.scripts.write_kb_draft_review_export",
            "--manifest",
            str(manifest_path),
            "--output",
            str(export_path),
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "app.scripts.write_kb_draft_review_static_ui",
            "--manifest",
            str(manifest_path),
            "--output",
            str(surface_path),
        ],
        check=True,
    )
    subprocess.run(
        [
            sys.executable,
            "-m",
            "app.scripts.validate_kb_draft_review_surface",
            "--surface",
            str(surface_path),
        ],
        check=True,
    )


def apply_claim_update(
    manifest: dict[str, Any],
    *,
    claim_id: str,
    decision: str,
    reviewer: str,
    notes: str,
    visual_acknowledged: bool,
) -> dict[str, Any]:
    previous = deepcopy(find_claim_task(manifest, claim_id))
    updated = update_claim_decision(
        manifest,
        claim_id=claim_id,
        decision=decision,
        reviewer=reviewer,
        notes=notes,
        visual_acknowledged=visual_acknowledged,
    )
    new_state = deepcopy(find_claim_task(updated, claim_id))
    append_audit_event(
        updated,
        action_type="CLAIM_DECISION_UPDATE",
        target_id=claim_id,
        reviewer=reviewer,
        previous_state=previous,
        new_state=new_state,
    )
    return updated


def apply_gap_update(
    manifest: dict[str, Any],
    *,
    gap_id: str,
    acknowledgement: str,
    reviewer: str,
    notes: str,
) -> dict[str, Any]:
    previous = deepcopy(find_gap_task(manifest, gap_id))
    updated = update_gap_acknowledgement(
        manifest,
        gap_id=gap_id,
        acknowledgement=acknowledgement,
        reviewer=reviewer,
        notes=notes,
    )
    new_state = deepcopy(find_gap_task(updated, gap_id))
    append_audit_event(
        updated,
        action_type="GAP_ACKNOWLEDGEMENT_UPDATE",
        target_id=gap_id,
        reviewer=reviewer,
        previous_state=previous,
        new_state=new_state,
    )
    return updated


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Apply a Gate 12 review mutation through Gate 10 contracts and regenerate review outputs.")
    parser.add_argument("--manifest", type=Path, default=root / "kbs" / "review" / "kb_draft_review_manifest.v1.json")
    parser.add_argument("--output", type=Path, help="Output manifest path. Defaults to overwriting --manifest.")
    parser.add_argument("--export-output", type=Path, default=root / "kbs" / "manifests" / "kb_draft_review_export.md")
    parser.add_argument("--surface-output", type=Path, default=root / "kbs" / "manifests" / "kb_draft_review_surface.html")
    parser.add_argument("--reviewer", required=True, help="Reviewer identifier for audit trail.")
    parser.add_argument("--notes", default="", help="Reviewer notes.")

    subparsers = parser.add_subparsers(dest="action", required=True)
    claim_parser = subparsers.add_parser("claim", help="Update a claim decision.")
    claim_parser.add_argument("claim_id")
    claim_parser.add_argument("decision", choices=["ACCEPT", "REJECT", "NEEDS_MORE_EVIDENCE", "UNSET"])
    claim_parser.add_argument("--visual-acknowledged", action="store_true")

    gap_parser = subparsers.add_parser("gap", help="Update an unresolved gap acknowledgement.")
    gap_parser.add_argument("gap_id")
    gap_parser.add_argument("acknowledgement", choices=["ACKNOWLEDGED", "NEEDS_MORE_EVIDENCE", "UNSET"])

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output = args.output or args.manifest
    manifest = read_json(args.manifest)

    if args.action == "claim":
        updated = apply_claim_update(
            manifest,
            claim_id=args.claim_id,
            decision=args.decision,
            reviewer=args.reviewer,
            notes=args.notes,
            visual_acknowledged=args.visual_acknowledged,
        )
        target_id = args.claim_id
    elif args.action == "gap":
        updated = apply_gap_update(
            manifest,
            gap_id=args.gap_id,
            acknowledgement=args.acknowledgement,
            reviewer=args.reviewer,
            notes=args.notes,
        )
        target_id = args.gap_id
    else:
        raise ValueError(f"Unsupported action: {args.action}")

    write_json(output, updated)
    validate_state(output)
    regenerate_outputs(output, export_path=args.export_output, surface_path=args.surface_output)

    print(f"Applied Gate 12 review update: {args.action} {target_id}")
    print(f"Wrote review manifest: {output}")
    print(f"Regenerated export: {args.export_output}")
    print(f"Regenerated surface: {args.surface_output}")
    print(f"Audit events: {updated.get('diagnostics', {}).get('review_audit_events', 0)}")


if __name__ == "__main__":
    main()
