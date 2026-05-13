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


def validate_provenance(manifest: dict[str, Any], *, min_events: int) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    events = manifest.get("review_audit_events") or []
    provenance_events = [event for event in events if event.get("request_provenance")]
    if len(provenance_events) < min_events:
        failures.append(
            ValidationFailure(
                "request_provenance.count",
                f"Expected at least {min_events} provenance-bearing audit event(s); found {len(provenance_events)}.",
            )
        )
    for index, event in enumerate(provenance_events):
        provenance = event.get("request_provenance") or {}
        for field in ["request_id", "route", "source", "user_agent", "remote_addr", "reviewer_role", "reviewer_display_name"]:
            if not provenance.get(field):
                failures.append(ValidationFailure(f"review_audit_events[{index}].request_provenance.{field}", "Missing provenance field."))
        if provenance.get("route") != "/review/update":
            failures.append(ValidationFailure(f"review_audit_events[{index}].request_provenance.route", "Expected /review/update."))
        if provenance.get("reviewer_role") != "reviewer":
            failures.append(ValidationFailure(f"review_audit_events[{index}].request_provenance.reviewer_role", "Expected reviewer role."))
    diagnostics = manifest.get("diagnostics") or {}
    if diagnostics.get("provenance_audit_events") != len(provenance_events):
        failures.append(ValidationFailure("diagnostics.provenance_audit_events", "Provenance diagnostic count mismatch."))
    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 15 request provenance audit fields.")
    parser.add_argument("--manifest", type=Path, default=root / "kbs" / "review" / "kb_draft_review_manifest.v1.json")
    parser.add_argument("--min-events", type=int, default=1)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate_provenance(read_json(args.manifest), min_events=args.min_events)
    if failures:
        print("[gate15:provenance] FAILED")
        for failure in failures:
            print(f"[gate15:provenance] {failure.check}: {failure.detail}")
        raise SystemExit(1)
    print("[gate15:provenance] OK")
    print(f"[gate15:provenance] manifest={args.manifest}")
    print(f"[gate15:provenance] min_events={args.min_events}")


if __name__ == "__main__":
    main()
