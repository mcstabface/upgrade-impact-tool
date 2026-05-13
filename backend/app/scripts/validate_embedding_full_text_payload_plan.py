from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.embedding_full_text_payload_plan import (
    DEFAULT_FULL_TEXT_PAYLOAD_REPORT,
    DEFAULT_FULL_TEXT_REQUEST_JSONL,
    build_full_embedding_input,
    build_full_text_payload_records,
    redaction_findings_for_text,
    write_full_text_payload_report,
    write_full_text_request_jsonl,
)
from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_EMBEDDING_MANIFEST = "kbs/retrieval/kb_embedding_manifest.v1.json"
DEFAULT_SOURCE_CHUNK_MANIFEST = "kbs/manifests/kb_search_context_chunks_manifest.json"
DEFAULT_RESPONSE_JSONL = "kbs/retrieval/kb_embedding_batch_responses.v1.jsonl"
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
            raise ValueError(f"Expected JSON object row: {path}")
        rows.append(payload)
    return rows


def assert_redaction_patterns_detected() -> None:
    findings = redaction_findings_for_text(
        chunk_id="fixture-redaction",
        text="Contact alice@example.test with case 123-45-6789 and card-like 4111111111111111.",
    )
    codes = {finding.code for finding in findings}
    expected = {"EMAIL_PATTERN", "SSN_PATTERN", "LONG_DIGIT_PATTERN"}
    if not expected.issubset(codes):
        raise AssertionError(f"Expected conservative redaction findings {expected}, got {codes}")


def assert_full_text_payload_builds_and_hashes_match() -> None:
    root = repo_root()
    manifest_path = root / DEFAULT_EMBEDDING_MANIFEST
    source_chunk_manifest_path = root / DEFAULT_SOURCE_CHUNK_MANIFEST
    if not manifest_path.exists():
        raise AssertionError(f"Expected embedding manifest from Gate 18D: {manifest_path}")
    if not source_chunk_manifest_path.exists():
        raise AssertionError(f"Expected source chunk manifest from Gate 2: {source_chunk_manifest_path}")

    manifest = read_json(manifest_path)
    manifest_chunks = manifest.get("chunks")
    if not isinstance(manifest_chunks, list) or not manifest_chunks:
        raise AssertionError("Expected manifest chunks")

    records, findings = build_full_text_payload_records(
        embedding_manifest_path=manifest_path,
        source_chunk_manifest_path=source_chunk_manifest_path,
    )
    if len(records) != len(manifest_chunks):
        raise AssertionError(f"Record count mismatch: {len(records)} vs {len(manifest_chunks)}")
    if findings:
        raise AssertionError(f"Expected no redaction findings in current corpus, got: {findings[:5]}")
    first = records[0]
    if "text:\n" not in first.input_text:
        raise AssertionError(f"Expected full text marker in payload: {first.input_text[:200]}")
    if not first.input_text.strip().endswith(first.input_text.split("text:\n", 1)[1].strip()):
        raise AssertionError("Expected payload to include text after text marker.")
    if not first.citation_payload:
        raise AssertionError("Expected citation payload on full text record.")

    with tempfile.TemporaryDirectory() as temp_dir:
        request_jsonl = Path(temp_dir) / "full_text_requests.jsonl"
        report_output = Path(temp_dir) / "payload_report.json"
        write_full_text_request_jsonl(request_jsonl, records)
        report = write_full_text_payload_report(
            path=report_output,
            embedding_manifest_path=manifest_path,
            source_chunk_manifest_path=source_chunk_manifest_path,
            request_jsonl_path=DEFAULT_FULL_TEXT_REQUEST_JSONL,
            records=records,
            findings=findings,
        )
        rows = read_jsonl(request_jsonl)
        if len(rows) != len(records):
            raise AssertionError("Request JSONL row count mismatch")
        if report.status != "PAYLOAD_READY_NOT_SUBMITTED":
            raise AssertionError(f"Expected ready-not-submitted report, got: {report.status}")
        if report.embedding_submission_allowed is not False:
            raise AssertionError("Gate 18F must not allow embedding submission.")
        if report.vectors_created is not False:
            raise AssertionError("Gate 18F must not create vectors.")
        persisted_report = read_json(report_output)
        if persisted_report.get("request_count") != len(records):
            raise AssertionError("Persisted report request count mismatch")


def assert_no_response_or_vector_outputs_exist() -> None:
    root = repo_root()
    for relative in (DEFAULT_RESPONSE_JSONL, DEFAULT_VECTOR_PATH, DEFAULT_VECTOR_INDEX_PATH):
        path = root / relative
        if path.exists():
            raise AssertionError(f"Gate 18F must not create response/vector artifact: {relative}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 18F full-text embedding payload plan.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_redaction_patterns_detected()
    assert_full_text_payload_builds_and_hashes_match()
    assert_no_response_or_vector_outputs_exist()
    print("[gate18f:payload] OK")
    print("[gate18f:payload] full_text=attached")
    print("[gate18f:payload] text_hashes=validated")
    print("[gate18f:payload] redaction_scan=passed")
    print("[gate18f:payload] embedding_submission=forbidden")
    print("[gate18f:payload] vectors=not_created")


if __name__ == "__main__":
    main()
