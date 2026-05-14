from __future__ import annotations

import argparse
import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.update_redaction_review_decisions import (
    ALLOWED_DECISIONS,
    DEFAULT_REVIEW_EXPORT_JSON,
    TERMINAL_DECISIONS,
    update_review_decision,
    validate_review_decision_export,
)


DEFAULT_RESPONSE_JSONL = "kbs/retrieval/kb_embedding_batch_responses.v1.jsonl"
DEFAULT_VECTOR_PATH = "kbs/retrieval/kb_vectors.v1.jsonl"
DEFAULT_VECTOR_INDEX_PATH = "kbs/retrieval/kb_vector_index.v1.json"


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def first_review_id(export: dict[str, Any]) -> str:
    items = export.get("items")
    if not isinstance(items, list) or not items:
        raise AssertionError("Expected review export to contain items")
    first = items[0]
    if not isinstance(first, dict):
        raise AssertionError("Expected first review item to be object")
    review_id = str(first.get("review_id") or "")
    if not review_id:
        raise AssertionError("First review item missing review_id")
    return review_id


def assert_update_requires_notes_for_terminal_decision() -> None:
    root = repo_root()
    source = root / DEFAULT_REVIEW_EXPORT_JSON
    if not source.exists():
        raise AssertionError(f"Expected Gate 18J review export: {source}")
    export = read_json(source)
    review_id = first_review_id(export)
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "review.json"
        write_json(path, copy.deepcopy(export))
        try:
            update_review_decision(
                export_path=path,
                review_id=review_id,
                decision="ALLOW_TECHNICAL_IDENTIFIER",
                notes="",
                reviewer="gate18k-validator",
            )
        except ValueError as exc:
            if "require reviewer notes" not in str(exc):
                raise AssertionError(f"Unexpected error for missing notes: {exc}") from exc
        else:
            raise AssertionError("Expected terminal decision without notes to fail")


def assert_update_applies_decision_without_enabling_submission() -> None:
    root = repo_root()
    source = root / DEFAULT_REVIEW_EXPORT_JSON
    export = read_json(source)
    review_id = first_review_id(export)
    initial_count = int(export.get("unresolved_count") or 0)
    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "review.json"
        write_json(path, copy.deepcopy(export))
        updated = update_review_decision(
            export_path=path,
            review_id=review_id,
            decision="ALLOW_TECHNICAL_IDENTIFIER",
            notes="Reviewed as technical identifier for dry-run validation.",
            reviewer="gate18k-validator",
        )
        errors = validate_review_decision_export(updated)
        if errors:
            raise AssertionError(f"Expected valid updated export, got: {errors}")
        if updated.get("embedding_submission_allowed") is not False:
            raise AssertionError("Decision update must not allow embedding submission")
        if updated.get("vectors_created") is not False:
            raise AssertionError("Decision update must not create vectors")
        if int(updated.get("unresolved_count") or 0) != initial_count:
            raise AssertionError("Decision update must not remove unresolved review items")
        summary = updated.get("decision_summary")
        if not isinstance(summary, dict):
            raise AssertionError("Updated export missing decision_summary")
        if summary.get("allow_technical_identifier_count") != 1:
            raise AssertionError(f"Expected one allow decision, got: {summary}")
        if summary.get("pending_count") != initial_count - 1:
            raise AssertionError(f"Expected pending count to decrease by one, got: {summary}")


def assert_unsupported_decision_fails_validation() -> None:
    invalid_export = {
        "embedding_submission_allowed": False,
        "vectors_created": False,
        "items": [
            {
                "review_id": "redaction-review-invalid",
                "reviewer_decision": "APPROVE_IT_I_GUESS",
                "reviewer_notes": "No.",
            }
        ],
    }
    errors = validate_review_decision_export(invalid_export)
    if not any("unsupported reviewer_decision" in error for error in errors):
        raise AssertionError(f"Expected unsupported decision error, got: {errors}")


def assert_no_response_or_vector_outputs_exist() -> None:
    root = repo_root()
    for relative in (DEFAULT_RESPONSE_JSONL, DEFAULT_VECTOR_PATH, DEFAULT_VECTOR_INDEX_PATH):
        if (root / relative).exists():
            raise AssertionError(f"Gate 18K must not create response/vector artifact: {relative}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 18K redaction review decision updates.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_update_requires_notes_for_terminal_decision()
    assert_update_applies_decision_without_enabling_submission()
    assert_unsupported_decision_fails_validation()
    assert_no_response_or_vector_outputs_exist()
    print("[gate18k:review-update] OK")
    print("[gate18k:review-update] terminal_decisions=require_notes")
    print("[gate18k:review-update] unresolved_items=preserved")
    print("[gate18k:review-update] embedding_submission=forbidden")
    print("[gate18k:review-update] vectors=not_created")


if __name__ == "__main__":
    main()
