from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.build_embedding_manifest_from_chunks import DEFAULT_SOURCE_CHUNK_MANIFEST, load_chunks_from_gate2_manifest
from app.scripts.embedding_batch_request_plan import (
    DEFAULT_EMBEDDING_MANIFEST,
    DEFAULT_REQUEST_JSONL,
    build_request_id,
    read_json,
    sha256_text,
)
from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_FULL_TEXT_REQUEST_JSONL = "kbs/retrieval/kb_embedding_full_text_requests.v1.jsonl"
DEFAULT_FULL_TEXT_PAYLOAD_REPORT = "kbs/retrieval/kb_embedding_full_text_payload_report.v1.json"

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
SSN_RE = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")
LONG_DIGIT_RE = re.compile(r"\b\d{13,19}\b")


@dataclass(frozen=True)
class PayloadRedactionFinding:
    code: str
    chunk_id: str
    detail: str


@dataclass(frozen=True)
class FullTextEmbeddingPayloadRecord:
    request_id: str
    chunk_id: str
    embedding_cache_key: str
    embedding_input_sha256: str
    chunk_text_sha256: str
    input_text: str
    model: str
    dimensions: int
    citation_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class FullTextPayloadReport:
    report_version: str
    status: str
    source_embedding_manifest: str
    source_chunk_manifest: str
    request_jsonl_path: str
    request_count: int
    redaction_check_status: str
    finding_count: int
    findings: list[PayloadRedactionFinding]
    embedding_submission_allowed: bool = False
    vectors_created: bool = False


def build_full_embedding_input(*, source_id: str, chunk_id: str, source_artifact_path: str, chunk_text: str) -> str:
    return f"source_id: {source_id}\nchunk_id: {chunk_id}\nsource_artifact_path: {source_artifact_path}\ntext:\n{chunk_text}"


def redaction_findings_for_text(*, chunk_id: str, text: str) -> list[PayloadRedactionFinding]:
    findings: list[PayloadRedactionFinding] = []
    if EMAIL_RE.search(text):
        findings.append(PayloadRedactionFinding("EMAIL_PATTERN", chunk_id, "Email-like text detected."))
    if SSN_RE.search(text):
        findings.append(PayloadRedactionFinding("SSN_PATTERN", chunk_id, "US SSN-like text detected."))
    if LONG_DIGIT_RE.search(text):
        findings.append(PayloadRedactionFinding("LONG_DIGIT_PATTERN", chunk_id, "Long digit sequence detected."))
    return findings


def chunks_by_id_from_source_manifest(source_chunk_manifest_path: Path) -> dict[str, dict[str, Any]]:
    chunks = load_chunks_from_gate2_manifest(source_chunk_manifest_path)
    by_id: dict[str, dict[str, Any]] = {}
    for chunk in chunks:
        chunk_id = str(chunk.get("chunk_id") or "")
        if not chunk_id:
            raise ValueError("Source chunk record missing chunk_id")
        if chunk_id in by_id:
            raise ValueError(f"Duplicate source chunk_id: {chunk_id}")
        by_id[chunk_id] = chunk
    return by_id


def build_full_text_payload_records(
    *,
    embedding_manifest_path: Path,
    source_chunk_manifest_path: Path,
) -> tuple[list[FullTextEmbeddingPayloadRecord], list[PayloadRedactionFinding]]:
    manifest = read_json(embedding_manifest_path)
    if manifest.get("status") != "SKELETON_NOT_EMBEDDED":
        raise ValueError("Embedding manifest must have SKELETON_NOT_EMBEDDED status")
    model = str(manifest.get("embedding_model") or "")
    dimensions = int(manifest.get("embedding_dimensions") or 0)
    if not model or dimensions <= 0:
        raise ValueError("Embedding model and dimensions are required")
    chunks = manifest.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        raise ValueError("Embedding manifest must contain chunks")

    source_chunks = chunks_by_id_from_source_manifest(source_chunk_manifest_path)
    records: list[FullTextEmbeddingPayloadRecord] = []
    findings: list[PayloadRedactionFinding] = []
    for index, manifest_chunk in enumerate(chunks):
        if not isinstance(manifest_chunk, dict):
            raise ValueError(f"manifest chunks[{index}] must be an object")
        chunk_id = str(manifest_chunk.get("chunk_id") or "")
        source_chunk = source_chunks.get(chunk_id)
        if source_chunk is None:
            raise ValueError(f"Chunk not found in source chunk manifest: {chunk_id}")
        chunk_text = str(source_chunk.get("chunk_text") or "")
        if not chunk_text:
            raise ValueError(f"Source chunk text missing for chunk: {chunk_id}")
        expected_text_sha = str(manifest_chunk.get("chunk_text_sha256") or "")
        actual_text_sha = sha256_text(chunk_text)
        if actual_text_sha != expected_text_sha:
            raise ValueError(f"Chunk text hash mismatch for {chunk_id}")

        citation_payload = manifest_chunk.get("citation_payload") or {}
        if not isinstance(citation_payload, dict):
            raise ValueError(f"citation_payload must be object for chunk: {chunk_id}")
        source_artifact_path = str(citation_payload.get("source_artifact_path") or source_chunk.get("source_path") or "")
        input_text = build_full_embedding_input(
            source_id=str(manifest_chunk.get("source_id") or ""),
            chunk_id=chunk_id,
            source_artifact_path=source_artifact_path,
            chunk_text=chunk_text,
        )
        actual_input_sha = sha256_text(input_text)
        expected_input_sha = str(manifest_chunk.get("embedding_input_sha256") or "")
        if actual_input_sha != expected_input_sha:
            raise ValueError(f"Embedding input hash mismatch for {chunk_id}")

        findings.extend(redaction_findings_for_text(chunk_id=chunk_id, text=chunk_text))
        cache_key = str(manifest_chunk.get("embedding_cache_key") or "")
        records.append(
            FullTextEmbeddingPayloadRecord(
                request_id=build_request_id(embedding_cache_key=cache_key),
                chunk_id=chunk_id,
                embedding_cache_key=cache_key,
                embedding_input_sha256=expected_input_sha,
                chunk_text_sha256=expected_text_sha,
                input_text=input_text,
                model=model,
                dimensions=dimensions,
                citation_payload=citation_payload,
            )
        )
    return records, findings


def write_full_text_request_jsonl(path: Path, records: list[FullTextEmbeddingPayloadRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(json.dumps(asdict(record), sort_keys=True) for record in records) + "\n", encoding="utf-8")


def write_full_text_payload_report(
    *,
    path: Path,
    embedding_manifest_path: Path,
    source_chunk_manifest_path: Path,
    request_jsonl_path: str,
    records: list[FullTextEmbeddingPayloadRecord],
    findings: list[PayloadRedactionFinding],
) -> FullTextPayloadReport:
    root = repo_root()
    report = FullTextPayloadReport(
        report_version="1",
        status="PAYLOAD_READY_NOT_SUBMITTED" if not findings else "PAYLOAD_BLOCKED_BY_REDACTION_FINDINGS",
        source_embedding_manifest=str(embedding_manifest_path.relative_to(root)) if embedding_manifest_path.is_relative_to(root) else str(embedding_manifest_path),
        source_chunk_manifest=str(source_chunk_manifest_path.relative_to(root)) if source_chunk_manifest_path.is_relative_to(root) else str(source_chunk_manifest_path),
        request_jsonl_path=request_jsonl_path,
        request_count=len(records),
        redaction_check_status="OK" if not findings else "FAILED",
        finding_count=len(findings),
        findings=findings,
        embedding_submission_allowed=False,
        vectors_created=False,
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build Gate 18F full-text embedding request payloads without submitting them.")
    parser.add_argument("--manifest", type=Path, default=root / DEFAULT_EMBEDDING_MANIFEST)
    parser.add_argument("--source-chunk-manifest", type=Path, default=root / DEFAULT_SOURCE_CHUNK_MANIFEST)
    parser.add_argument("--request-jsonl-output", type=Path, default=root / DEFAULT_FULL_TEXT_REQUEST_JSONL)
    parser.add_argument("--report-output", type=Path, default=root / DEFAULT_FULL_TEXT_PAYLOAD_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    records, findings = build_full_text_payload_records(
        embedding_manifest_path=args.manifest,
        source_chunk_manifest_path=args.source_chunk_manifest,
    )
    write_full_text_request_jsonl(args.request_jsonl_output, records)
    report = write_full_text_payload_report(
        path=args.report_output,
        embedding_manifest_path=args.manifest,
        source_chunk_manifest_path=args.source_chunk_manifest,
        request_jsonl_path=str(args.request_jsonl_output.relative_to(repo_root())) if args.request_jsonl_output.is_relative_to(repo_root()) else str(args.request_jsonl_output),
        records=records,
        findings=findings,
    )
    print(f"[gate18f:payload] Wrote full-text request JSONL: {args.request_jsonl_output}")
    print(f"[gate18f:payload] Wrote payload report: {args.report_output}")
    print(f"[gate18f:payload] requests={len(records)}")
    print(f"[gate18f:payload] redaction_findings={report.finding_count}")
    print("[gate18f:payload] embedding_submission=forbidden")


if __name__ == "__main__":
    main()
