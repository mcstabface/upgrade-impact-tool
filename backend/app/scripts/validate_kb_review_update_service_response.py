from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


@dataclass(frozen=True)
class ValidationFailure:
    check: str
    detail: str


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_response(response: dict[str, Any], *, expected_action: str, expected_target_id: str, min_audit_events: int) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    if response.get("status") != "OK":
        failures.append(ValidationFailure("status", f"Expected OK; found {response.get('status')!r}."))
    if response.get("action") != expected_action:
        failures.append(ValidationFailure("action", f"Expected {expected_action!r}; found {response.get('action')!r}."))
    if response.get("target_id") != expected_target_id:
        failures.append(ValidationFailure("target_id", f"Expected {expected_target_id!r}; found {response.get('target_id')!r}."))
    if not response.get("reviewer"):
        failures.append(ValidationFailure("reviewer", "Expected non-empty reviewer."))
    if response.get("review_status") not in {"IN_REVIEW", "PENDING_REVIEW", "REVIEW_COMPLETE"}:
        failures.append(ValidationFailure("review_status", f"Unexpected review status: {response.get('review_status')!r}."))
    if int(response.get("audit_event_count") or 0) < min_audit_events:
        failures.append(
            ValidationFailure(
                "audit_event_count",
                f"Expected at least {min_audit_events}; found {response.get('audit_event_count')!r}.",
            )
        )
    diagnostics = response.get("diagnostics") or {}
    if diagnostics.get("review_audit_events") != response.get("audit_event_count"):
        failures.append(ValidationFailure("diagnostics.review_audit_events", "Diagnostic audit count must match response audit_event_count."))
    for field in ["manifest_path", "export_path", "surface_path"]:
        if not response.get(field):
            failures.append(ValidationFailure(field, "Expected output path in response."))
    messages = response.get("messages") or []
    expected_fragments = ["Gate 12 bridge", "validated", "regenerated"]
    message_text = " ".join(str(message) for message in messages).lower()
    for fragment in expected_fragments:
        if fragment.lower() not in message_text:
            failures.append(ValidationFailure("messages", f"Expected response messages to mention {fragment!r}."))
    return failures


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate Gate 13 review update service response.")
    parser.add_argument("response", type=Path, help="Response JSON path.")
    parser.add_argument("--expected-action", required=True, choices=["claim", "gap"])
    parser.add_argument("--expected-target-id", required=True)
    parser.add_argument("--min-audit-events", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate_response(
        read_json(args.response),
        expected_action=args.expected_action,
        expected_target_id=args.expected_target_id,
        min_audit_events=args.min_audit_events,
    )
    if failures:
        print("[gate13:response] FAILED")
        for failure in failures:
            print(f"[gate13:response] {failure.check}: {failure.detail}")
        raise SystemExit(1)
    print("[gate13:response] OK")
    print(f"[gate13:response] response={args.response}")


if __name__ == "__main__":
    main()
