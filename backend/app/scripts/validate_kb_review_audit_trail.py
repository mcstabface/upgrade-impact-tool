from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root

ALLOWED_ACTION_TYPES = {"CLAIM_DECISION_UPDATE", "GAP_ACKNOWLEDGEMENT_UPDATE"}


@dataclass(frozen=True)
class ValidationFailure:
    check: str
    detail: str


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_audit_trail(manifest: dict[str, Any], *, min_events: int) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    events = manifest.get("review_audit_events") or []
    if len(events) < min_events:
        failures.append(ValidationFailure("review_audit_events.count", f"Expected at least {min_events} audit event(s); found {len(events)}."))

    seen_event_ids: set[str] = set()
    for index, event in enumerate(events):
        if not isinstance(event, dict):
            failures.append(ValidationFailure(f"review_audit_events[{index}]", "Expected audit event object."))
            continue
        for field in ["event_id", "timestamp_utc", "action_type", "target_id", "reviewer", "previous_state", "new_state"]:
            if field not in event:
                failures.append(ValidationFailure(f"review_audit_events[{index}].{field}", "Missing required audit field."))
        event_id = event.get("event_id")
        if event_id in seen_event_ids:
            failures.append(ValidationFailure(f"review_audit_events[{index}].event_id", f"Duplicate event ID: {event_id}."))
        seen_event_ids.add(str(event_id))
        if event.get("action_type") not in ALLOWED_ACTION_TYPES:
            failures.append(ValidationFailure(f"review_audit_events[{index}].action_type", f"Unsupported action type: {event.get('action_type')!r}."))
        if not event.get("reviewer") or event.get("reviewer") == "UNSPECIFIED_REVIEWER":
            failures.append(ValidationFailure(f"review_audit_events[{index}].reviewer", "Audit event requires explicit reviewer."))
        previous_state = event.get("previous_state")
        new_state = event.get("new_state")
        if previous_state == new_state:
            failures.append(ValidationFailure(f"review_audit_events[{index}].state_delta", "Previous and new state are identical."))
        if not isinstance(previous_state, dict) or not isinstance(new_state, dict):
            failures.append(ValidationFailure(f"review_audit_events[{index}].state", "Previous/new state must be objects."))
        elif event.get("action_type") == "CLAIM_DECISION_UPDATE":
            if previous_state.get("reviewer_decision") == new_state.get("reviewer_decision"):
                failures.append(
                    ValidationFailure(
                        f"review_audit_events[{index}].reviewer_decision",
                        "Claim decision audit event did not change reviewer_decision.",
                    )
                )
        elif event.get("action_type") == "GAP_ACKNOWLEDGEMENT_UPDATE":
            if previous_state.get("acknowledgement_status") == new_state.get("acknowledgement_status"):
                failures.append(
                    ValidationFailure(
                        f"review_audit_events[{index}].acknowledgement_status",
                        "Gap acknowledgement audit event did not change acknowledgement_status.",
                    )
                )

    diagnostics = manifest.get("diagnostics") or {}
    if diagnostics.get("review_audit_events") != len(events):
        failures.append(ValidationFailure("diagnostics.review_audit_events", "Audit-event diagnostic count mismatch."))

    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 12 review mutation audit trail.")
    parser.add_argument("--manifest", type=Path, default=root / "kbs" / "review" / "kb_draft_review_manifest.v1.json")
    parser.add_argument("--min-events", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate_audit_trail(read_json(args.manifest), min_events=args.min_events)
    if failures:
        print("[gate12:audit] FAILED")
        for failure in failures:
            print(f"[gate12:audit] {failure.check}: {failure.detail}")
        raise SystemExit(1)
    print("[gate12:audit] OK")
    print(f"[gate12:audit] manifest={args.manifest}")
    print(f"[gate12:audit] min_events={args.min_events}")


if __name__ == "__main__":
    main()
