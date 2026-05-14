from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_REVIEW_EXPORT_JSON = "kbs/retrieval/kb_embedding_unresolved_redaction_review.v1.json"

ALLOWED_DECISIONS = {
    "PENDING",
    "ALLOW_TECHNICAL_IDENTIFIER",
    "MASK_BEFORE_EMBEDDING",
    "BLOCK_EMBEDDING",
}
TERMINAL_DECISIONS = ALLOWED_DECISIONS - {"PENDING"}


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def items_by_review_id(export: dict[str, Any]) -> dict[str, dict[str, Any]]:
    items = export.get("items")
    if not isinstance(items, list):
        raise ValueError("Review export items must be a list")
    by_id: dict[str, dict[str, Any]] = {}
    for item in items:
        if not isinstance(item, dict):
            raise ValueError("Review export item must be an object")
        review_id = str(item.get("review_id") or "")
        if not review_id:
            raise ValueError("Review export item missing review_id")
        if review_id in by_id:
            raise ValueError(f"Duplicate review_id: {review_id}")
        by_id[review_id] = item
    return by_id


def update_review_decision(
    *,
    export_path: Path,
    review_id: str,
    decision: str,
    notes: str,
    reviewer: str,
) -> dict[str, Any]:
    decision = decision.strip()
    if decision not in ALLOWED_DECISIONS:
        raise ValueError(f"Unsupported reviewer decision: {decision}")
    if decision in TERMINAL_DECISIONS and not notes.strip():
        raise ValueError("Terminal redaction review decisions require reviewer notes")
    if not reviewer.strip():
        raise ValueError("reviewer is required")

    export = read_json(export_path)
    if export.get("embedding_submission_allowed") is not False:
        raise ValueError("Review export must keep embedding_submission_allowed false")
    by_id = items_by_review_id(export)
    if review_id not in by_id:
        raise ValueError(f"Unknown review_id: {review_id}")

    item = by_id[review_id]
    item["reviewer_decision"] = decision
    item["reviewer_notes"] = notes
    item["reviewer"] = reviewer

    items = export.get("items")
    assert isinstance(items, list)
    pending_count = sum(1 for current in items if isinstance(current, dict) and current.get("reviewer_decision") == "PENDING")
    terminal_count = sum(1 for current in items if isinstance(current, dict) and current.get("reviewer_decision") in TERMINAL_DECISIONS)
    export["decision_summary"] = {
        "pending_count": pending_count,
        "terminal_decision_count": terminal_count,
        "allow_technical_identifier_count": sum(
            1 for current in items if isinstance(current, dict) and current.get("reviewer_decision") == "ALLOW_TECHNICAL_IDENTIFIER"
        ),
        "mask_before_embedding_count": sum(
            1 for current in items if isinstance(current, dict) and current.get("reviewer_decision") == "MASK_BEFORE_EMBEDDING"
        ),
        "block_embedding_count": sum(
            1 for current in items if isinstance(current, dict) and current.get("reviewer_decision") == "BLOCK_EMBEDDING"
        ),
    }
    export["status"] = "REVIEW_COMPLETE" if pending_count == 0 else "REVIEW_IN_PROGRESS"
    export["embedding_submission_allowed"] = False
    export["vectors_created"] = False
    write_json(export_path, export)
    return export


def validate_review_decision_export(export: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if export.get("embedding_submission_allowed") is not False:
        errors.append("embedding_submission_allowed must remain false")
    if export.get("vectors_created") is not False:
        errors.append("vectors_created must remain false")
    items = export.get("items")
    if not isinstance(items, list):
        return errors + ["items must be a list"]
    for item in items:
        if not isinstance(item, dict):
            errors.append("item must be object")
            continue
        decision = item.get("reviewer_decision")
        if decision not in ALLOWED_DECISIONS:
            errors.append(f"unsupported reviewer_decision: {decision}")
        if decision in TERMINAL_DECISIONS and not str(item.get("reviewer_notes") or "").strip():
            errors.append(f"terminal decision requires notes: {item.get('review_id')}")
    return errors


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Update Gate 18K unresolved redaction review decision.")
    parser.add_argument("--review-export", type=Path, default=root / DEFAULT_REVIEW_EXPORT_JSON)
    parser.add_argument("--review-id", required=True)
    parser.add_argument("--decision", required=True, choices=sorted(ALLOWED_DECISIONS))
    parser.add_argument("--notes", default="")
    parser.add_argument("--reviewer", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    export = update_review_decision(
        export_path=args.review_export,
        review_id=args.review_id,
        decision=args.decision,
        notes=args.notes,
        reviewer=args.reviewer,
    )
    errors = validate_review_decision_export(export)
    if errors:
        for error in errors:
            print(f"[gate18k:review-update] {error}")
        raise SystemExit(1)
    summary = export.get("decision_summary", {})
    print("[gate18k:review-update] OK")
    print(f"[gate18k:review-update] review_id={args.review_id}")
    print(f"[gate18k:review-update] decision={args.decision}")
    print(f"[gate18k:review-update] pending_count={summary.get('pending_count')}")
    print("[gate18k:review-update] embedding_submission=forbidden")


if __name__ == "__main__":
    main()
