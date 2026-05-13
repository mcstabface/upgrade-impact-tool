from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.embedding_batch_request_plan import (
    DEFAULT_EMBEDDING_MANIFEST,
    DEFAULT_REQUEST_JSONL,
    DEFAULT_REQUEST_PLAN,
    DEFAULT_RESPONSE_JSONL,
    build_request_plan,
    write_request_jsonl,
    write_request_plan,
)
from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_VECTOR_PATH = "kbs/retrieval/kb_vectors.v1.jsonl"
DEFAULT_VECTOR_INDEX_PATH = "kbs/retrieval/kb_vector_index.v1.json"


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSONL object row: {path}")
        rows.append(payload)
    return rows


def assert_plan_builds_and_writes() -> None:
    root = repo_root()
    manifest_path = root / DEFAULT_EMBEDDING_MANIFEST
    if not manifest_path.exists():
        raise AssertionError(f"Expected Gate 18D manifest to exist: {manifest_path}")
    manifest = read_json(manifest_path)
    chunks = manifest.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        raise AssertionError("Expected persisted embedding manifest to contain chunks.")

    with tempfile.TemporaryDirectory() as temp_dir:
        plan_output = Path(temp_dir) / "request_plan.json"
        request_jsonl_output = Path(temp_dir) / "requests.jsonl"
        plan = build_request_plan(manifest_path=manifest_path, batch_size=128, max_retries=3)
        write_request_plan(plan_output, plan)
        write_request_jsonl(request_jsonl_output, plan)

        if not plan_output.exists():
            raise AssertionError("Expected request plan JSON to be written.")
        if not request_jsonl_output.exists():
            raise AssertionError("Expected request JSONL to be written.")
        if plan.status != "REQUEST_PLAN_NOT_SUBMITTED":
            raise AssertionError(f"Expected non-submitted status, got: {plan.status}")
        if plan.source_embedding_manifest != DEFAULT_EMBEDDING_MANIFEST:
            raise AssertionError(f"Unexpected source manifest path: {plan.source_embedding_manifest}")
        if plan.request_jsonl_path != DEFAULT_REQUEST_JSONL:
            raise AssertionError(f"Unexpected request JSONL path: {plan.request_jsonl_path}")
        if plan.expected_response_jsonl_path != DEFAULT_RESPONSE_JSONL:
            raise AssertionError(f"Unexpected response JSONL path: {plan.expected_response_jsonl_path}")
        if plan.request_count != len(chunks):
            raise AssertionError(f"Request count mismatch: {plan.request_count} vs {len(chunks)}")
        if plan.batch_count < 1:
            raise AssertionError("Expected at least one batch.")
        if sum(batch.item_count for batch in plan.batches) != plan.request_count:
            raise AssertionError("Batch item counts must sum to request count.")

        persisted_plan = read_json(plan_output)
        request_rows = read_jsonl(request_jsonl_output)
        if persisted_plan.get("request_count") != len(request_rows):
            raise AssertionError("Request plan count must match JSONL row count.")
        seen_request_ids: set[str] = set()
        for row in request_rows:
            request_id = str(row.get("request_id") or "")
            if not request_id.startswith("embreq_"):
                raise AssertionError(f"Invalid request_id: {row}")
            if request_id in seen_request_ids:
                raise AssertionError(f"Duplicate request_id: {request_id}")
            seen_request_ids.add(request_id)
            if not row.get("embedding_cache_key"):
                raise AssertionError(f"Missing embedding_cache_key: {row}")
            if not row.get("embedding_input_sha256"):
                raise AssertionError(f"Missing embedding_input_sha256: {row}")
            if not row.get("citation_payload"):
                raise AssertionError(f"Missing citation_payload: {row}")
            if "vector" in row:
                raise AssertionError(f"Request row must not contain vector values: {row}")


def assert_no_vector_outputs_exist() -> None:
    root = repo_root()
    for relative in (DEFAULT_VECTOR_PATH, DEFAULT_VECTOR_INDEX_PATH, DEFAULT_RESPONSE_JSONL):
        path = root / relative
        if path.exists():
            raise AssertionError(f"Gate 18E must not create response/vector artifact: {relative}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 18E embedding batch request plan.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_plan_builds_and_writes()
    assert_no_vector_outputs_exist()
    print("[gate18e:request-plan] OK")
    print("[gate18e:request-plan] request_plan=valid")
    print("[gate18e:request-plan] request_jsonl=valid")
    print("[gate18e:request-plan] idempotency=request_ids_cache_keys")
    print("[gate18e:request-plan] embedding_submission=forbidden")
    print("[gate18e:request-plan] vectors=not_created")


if __name__ == "__main__":
    main()
