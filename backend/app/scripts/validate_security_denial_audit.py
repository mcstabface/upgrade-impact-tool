from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


@dataclass(frozen=True)
class ValidationFailure:
    check: str
    detail: str


def read_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Security denial audit file not found: {path}")
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def compute_hash_without_event_hash(event: dict[str, Any]) -> str:
    payload = dict(event)
    payload.pop("event_hash", None)
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def validate_audit(path: Path, *, min_events: int) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    events = read_events(path)
    if len(events) < min_events:
        failures.append(ValidationFailure("event_count", f"Expected at least {min_events} events; found {len(events)}."))
    previous_hash = "GENESIS"
    seen_ids: set[str] = set()
    for index, event in enumerate(events):
        for field in [
            "event_id",
            "timestamp_utc",
            "event_type",
            "request_id",
            "route",
            "action",
            "target_id",
            "reviewer_id",
            "principal_subject",
            "principal_issuer",
            "decision",
            "denial_reason",
            "source",
            "user_agent",
            "finalization_allowed",
            "previous_hash",
            "event_hash",
        ]:
            if field not in event:
                failures.append(ValidationFailure(f"events[{index}].{field}", "Missing required field."))
        if event.get("event_id") in seen_ids:
            failures.append(ValidationFailure(f"events[{index}].event_id", f"Duplicate event ID: {event.get('event_id')}."))
        seen_ids.add(str(event.get("event_id")))
        if event.get("event_type") != "SECURITY_DENIAL":
            failures.append(ValidationFailure(f"events[{index}].event_type", "Expected SECURITY_DENIAL."))
        if event.get("decision") != "DENIED":
            failures.append(ValidationFailure(f"events[{index}].decision", "Expected DENIED."))
        if event.get("finalization_allowed") is not False:
            failures.append(ValidationFailure(f"events[{index}].finalization_allowed", "Expected finalization_allowed=false."))
        if event.get("previous_hash") != previous_hash:
            failures.append(
                ValidationFailure(
                    f"events[{index}].previous_hash",
                    f"Expected previous hash {previous_hash!r}; found {event.get('previous_hash')!r}.",
                )
            )
        expected_hash = compute_hash_without_event_hash(event)
        if event.get("event_hash") != expected_hash:
            failures.append(ValidationFailure(f"events[{index}].event_hash", "Event hash does not match event payload."))
        previous_hash = str(event.get("event_hash"))
    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 16B security denial audit JSONL.")
    parser.add_argument("--audit", type=Path, default=root / "kbs" / "audit" / "security_denials.jsonl")
    parser.add_argument("--min-events", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate_audit(args.audit, min_events=args.min_events)
    if failures:
        print("[gate16b:audit] FAILED")
        for failure in failures:
            print(f"[gate16b:audit] {failure.check}: {failure.detail}")
        raise SystemExit(1)
    print("[gate16b:audit] OK")
    print(f"[gate16b:audit] audit={args.audit}")
    print(f"[gate16b:audit] min_events={args.min_events}")


if __name__ == "__main__":
    main()
