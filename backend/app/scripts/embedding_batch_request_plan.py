from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_EMBEDDING_MANIFEST = "kbs/retrieval/kb_embedding_manifest.v1.json"
DEFAULT_REQUEST_PLAN = "kbs/retrieval/kb_embedding_batch_request_plan.v1.json"
DEFAULT_REQUEST_JSONL = "kbs/retrieval/kb_embedding_batch_requests.v1.jsonl"
DEFAULT_RESPONSE_JSONL = "kbs/retrieval/kb_embedding_batch_responses.v1.jsonl"
DEFAULT_BATCH_SIZE = 128
DEFAULT_MAX_RETRIES = 3


@dataclass(frozen=True)
class EmbeddingBatchRequestItem:
    request_id: str
    chunk_id: str
    embedding_cache_key: str
    embedding_input_sha256: str
    input_text: str
    model: str
    dimensions: int
    citation_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddingBatchRequestGroup:
    batch_id: str
    item_count: int
    request_ids: list[str]


@dataclass(frozen=True)
class EmbeddingBatchRequestPlan:
    plan_version: str
    status: str
    source_embedding_manifest: str
    source_embedding_manifest_sha256: str
    request_jsonl_path: str
    expected_response_jsonl_path: str
    batch_size: int
    max_retries: int
    embedding_model: str
    embedding_dimensions: int
    request_count: int
    batch_count: int
    requests: list[EmbeddingBatchRequestItem]
    batches: list[EmbeddingBatchRequestGroup]


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def build_embedding_input_from_manifest_chunk(chunk: dict[str, Any]) -> str:
    source_id = str(chunk.get("source_id") or "")
    chunk_id = str(chunk.get("chunk_id") or "")
    citation_payload = chunk.get("citation_payload") if isinstance(chunk.get("citation_payload"), dict) else {}
    source_artifact_path = str(citation_payload.get("source_artifact_path") or chunk.get("source_path") or "")
    return f"source_id: {source_id}\nchunk_id: {chunk_id}\nsource_artifact_path: {source_artifact_path}\ntext_sha256: {chunk.get('chunk_text_sha256')}\n"


def build_request_id(*, embedding_cache_key: str) -> str:
    return f"embreq_{embedding_cache_key[:24]}"


def build_batch_id(*, batch_index: int, request_ids: list[str]) -> str:
    material = f"batch:{batch_index}:" + "|".join(request_ids)
    return f"embbatch_{sha256_text(material)[:24]}"


def build_request_plan(
    *,
    manifest_path: Path,
    request_plan_path: str = DEFAULT_REQUEST_PLAN,
    request_jsonl_path: str = DEFAULT_REQUEST_JSONL,
    response_jsonl_path: str = DEFAULT_RESPONSE_JSONL,
    batch_size: int = DEFAULT_BATCH_SIZE,
    max_retries: int = DEFAULT_MAX_RETRIES,
) -> EmbeddingBatchRequestPlan:
    if batch_size <= 0:
        raise ValueError("batch_size must be positive")
    if max_retries < 0:
        raise ValueError("max_retries must be non-negative")

    manifest = read_json(manifest_path)
    if manifest.get("status") != "SKELETON_NOT_EMBEDDED":
        raise ValueError("source embedding manifest must have status SKELETON_NOT_EMBEDDED")
    chunks = manifest.get("chunks")
    if not isinstance(chunks, list) or not chunks:
        raise ValueError("source embedding manifest must contain chunks")

    model = str(manifest.get("embedding_model") or "")
    dimensions = int(manifest.get("embedding_dimensions") or 0)
    if not model:
        raise ValueError("embedding_model is required")
    if dimensions <= 0:
        raise ValueError("embedding_dimensions must be positive")

    requests: list[EmbeddingBatchRequestItem] = []
    seen_request_ids: set[str] = set()
    for index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            raise ValueError(f"chunks[{index}] must be an object")
        chunk_id = str(chunk.get("chunk_id") or "")
        cache_key = str(chunk.get("embedding_cache_key") or "")
        input_sha = str(chunk.get("embedding_input_sha256") or "")
        if not chunk_id or not cache_key or not input_sha:
            raise ValueError(f"chunks[{index}] missing required request identity fields")
        request_id = build_request_id(embedding_cache_key=cache_key)
        if request_id in seen_request_ids:
            raise ValueError(f"duplicate request_id: {request_id}")
        seen_request_ids.add(request_id)
        citation_payload = chunk.get("citation_payload") or {}
        if not isinstance(citation_payload, dict):
            raise ValueError(f"chunks[{index}] citation_payload must be object")
        requests.append(
            EmbeddingBatchRequestItem(
                request_id=request_id,
                chunk_id=chunk_id,
                embedding_cache_key=cache_key,
                embedding_input_sha256=input_sha,
                input_text=build_embedding_input_from_manifest_chunk(chunk),
                model=model,
                dimensions=dimensions,
                citation_payload=citation_payload,
            )
        )

    batches: list[EmbeddingBatchRequestGroup] = []
    for batch_index, start in enumerate(range(0, len(requests), batch_size)):
        batch_requests = requests[start : start + batch_size]
        request_ids = [request.request_id for request in batch_requests]
        batches.append(
            EmbeddingBatchRequestGroup(
                batch_id=build_batch_id(batch_index=batch_index, request_ids=request_ids),
                item_count=len(batch_requests),
                request_ids=request_ids,
            )
        )

    root = repo_root()
    source_embedding_manifest = str(manifest_path.relative_to(root)) if manifest_path.is_relative_to(root) else str(manifest_path)
    return EmbeddingBatchRequestPlan(
        plan_version="1",
        status="REQUEST_PLAN_NOT_SUBMITTED",
        source_embedding_manifest=source_embedding_manifest,
        source_embedding_manifest_sha256=sha256_file(manifest_path),
        request_jsonl_path=request_jsonl_path,
        expected_response_jsonl_path=response_jsonl_path,
        batch_size=batch_size,
        max_retries=max_retries,
        embedding_model=model,
        embedding_dimensions=dimensions,
        request_count=len(requests),
        batch_count=len(batches),
        requests=requests,
        batches=batches,
    )


def write_request_plan(path: Path, plan: EmbeddingBatchRequestPlan) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(plan), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_request_jsonl(path: Path, plan: EmbeddingBatchRequestPlan) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for request in plan.requests:
        lines.append(json.dumps(asdict(request), sort_keys=True))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build Gate 18E embedding batch request plan without submitting requests.")
    parser.add_argument("--manifest", type=Path, default=root / DEFAULT_EMBEDDING_MANIFEST)
    parser.add_argument("--plan-output", type=Path, default=root / DEFAULT_REQUEST_PLAN)
    parser.add_argument("--request-jsonl-output", type=Path, default=root / DEFAULT_REQUEST_JSONL)
    parser.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    parser.add_argument("--max-retries", type=int, default=DEFAULT_MAX_RETRIES)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    plan = build_request_plan(
        manifest_path=args.manifest,
        batch_size=args.batch_size,
        max_retries=args.max_retries,
    )
    write_request_plan(args.plan_output, plan)
    write_request_jsonl(args.request_jsonl_output, plan)
    print(f"[gate18e:plan] Wrote embedding batch request plan: {args.plan_output}")
    print(f"[gate18e:plan] Wrote embedding batch request JSONL: {args.request_jsonl_output}")
    print(f"[gate18e:plan] requests={plan.request_count}")
    print(f"[gate18e:plan] batches={plan.batch_count}")
    print("[gate18e:plan] embedding_submission=forbidden")


if __name__ == "__main__":
    main()
