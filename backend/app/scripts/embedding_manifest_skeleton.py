from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


MANIFEST_VERSION = "1"
MANIFEST_STATUS = "SKELETON_NOT_EMBEDDED"
DEFAULT_EMBEDDING_PROVIDER = "openai"
DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"
DEFAULT_EMBEDDING_DIMENSIONS = 1536
DEFAULT_INPUT_POLICY = "chunk_text_with_stable_metadata_prefix_v1"
DEFAULT_CACHE_KEY_POLICY = "sha256(model|dimensions|input_policy|chunk_id|chunk_text_sha256)"
DEFAULT_VECTOR_STORE_KIND = "local_jsonl_float32"
DEFAULT_VECTOR_PATH = "kbs/retrieval/kb_vectors.v1.jsonl"
DEFAULT_VECTOR_INDEX_PATH = "kbs/retrieval/kb_vector_index.v1.json"


@dataclass(frozen=True)
class EmbeddingVectorStoreSpec:
    kind: str = DEFAULT_VECTOR_STORE_KIND
    path: str = DEFAULT_VECTOR_PATH
    index_path: str = DEFAULT_VECTOR_INDEX_PATH


@dataclass(frozen=True)
class EmbeddingChunkRecord:
    chunk_id: str
    source_id: str
    source_path: str
    source_span: dict[str, int]
    chunk_text_sha256: str
    embedding_input_sha256: str
    embedding_cache_key: str
    vector_record_id: str
    citation_payload: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EmbeddingManifestSkeleton:
    manifest_version: str
    status: str
    source_chunk_manifest: str
    source_chunk_manifest_sha256: str
    embedding_provider: str
    embedding_model: str
    embedding_dimensions: int
    embedding_input_policy: str
    embedding_cache_key_policy: str
    vector_store: EmbeddingVectorStoreSpec
    chunks: list[EmbeddingChunkRecord]


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def build_embedding_input(*, source_id: str, chunk_id: str, chunk_text: str) -> str:
    return f"source_id: {source_id}\nchunk_id: {chunk_id}\ntext:\n{chunk_text}"


def build_embedding_cache_key(
    *,
    model: str,
    dimensions: int,
    input_policy: str,
    chunk_id: str,
    chunk_text_sha256: str,
) -> str:
    material = f"{model}|{dimensions}|{input_policy}|{chunk_id}|{chunk_text_sha256}"
    return sha256_text(material)


def build_vector_record_id(*, embedding_cache_key: str) -> str:
    return f"vec_{embedding_cache_key[:24]}"


def build_chunk_record(
    chunk: dict[str, Any],
    *,
    model: str = DEFAULT_EMBEDDING_MODEL,
    dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS,
    input_policy: str = DEFAULT_INPUT_POLICY,
) -> EmbeddingChunkRecord:
    chunk_id = str(chunk.get("chunk_id") or "").strip()
    source_id = str(chunk.get("source_id") or "").strip()
    chunk_text = str(chunk.get("chunk_text") or "")
    if not chunk_id:
        raise ValueError("chunk_id is required")
    if not source_id:
        raise ValueError("source_id is required")
    if not chunk_text.strip():
        raise ValueError("chunk_text is required")

    source_path = str(chunk.get("source_path") or "")
    source_span_value = chunk.get("source_span") or {"start": 0, "end": 0}
    if not isinstance(source_span_value, dict):
        raise ValueError("source_span must be an object")
    source_span = {
        "start": int(source_span_value.get("start", 0)),
        "end": int(source_span_value.get("end", 0)),
    }
    citation_payload = chunk.get("citation_payload") or {}
    if not isinstance(citation_payload, dict):
        raise ValueError("citation_payload must be an object")

    chunk_text_sha256 = sha256_text(chunk_text)
    embedding_input = build_embedding_input(source_id=source_id, chunk_id=chunk_id, chunk_text=chunk_text)
    embedding_input_sha256 = sha256_text(embedding_input)
    embedding_cache_key = build_embedding_cache_key(
        model=model,
        dimensions=dimensions,
        input_policy=input_policy,
        chunk_id=chunk_id,
        chunk_text_sha256=chunk_text_sha256,
    )
    return EmbeddingChunkRecord(
        chunk_id=chunk_id,
        source_id=source_id,
        source_path=source_path,
        source_span=source_span,
        chunk_text_sha256=chunk_text_sha256,
        embedding_input_sha256=embedding_input_sha256,
        embedding_cache_key=embedding_cache_key,
        vector_record_id=build_vector_record_id(embedding_cache_key=embedding_cache_key),
        citation_payload=citation_payload,
    )


def build_embedding_manifest_skeleton(
    *,
    source_chunk_manifest: str,
    source_chunk_manifest_sha256: str,
    chunks: list[dict[str, Any]],
    embedding_provider: str = DEFAULT_EMBEDDING_PROVIDER,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    embedding_dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS,
    embedding_input_policy: str = DEFAULT_INPUT_POLICY,
) -> EmbeddingManifestSkeleton:
    records = [
        build_chunk_record(
            chunk,
            model=embedding_model,
            dimensions=embedding_dimensions,
            input_policy=embedding_input_policy,
        )
        for chunk in chunks
    ]
    return EmbeddingManifestSkeleton(
        manifest_version=MANIFEST_VERSION,
        status=MANIFEST_STATUS,
        source_chunk_manifest=source_chunk_manifest,
        source_chunk_manifest_sha256=source_chunk_manifest_sha256,
        embedding_provider=embedding_provider,
        embedding_model=embedding_model,
        embedding_dimensions=embedding_dimensions,
        embedding_input_policy=embedding_input_policy,
        embedding_cache_key_policy=DEFAULT_CACHE_KEY_POLICY,
        vector_store=EmbeddingVectorStoreSpec(),
        chunks=records,
    )


def manifest_to_dict(manifest: EmbeddingManifestSkeleton) -> dict[str, Any]:
    return asdict(manifest)


def write_embedding_manifest_skeleton(path: Path, manifest: EmbeddingManifestSkeleton) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest_to_dict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def validate_embedding_manifest_skeleton(manifest: EmbeddingManifestSkeleton) -> list[str]:
    errors: list[str] = []
    if manifest.manifest_version != MANIFEST_VERSION:
        errors.append("manifest_version must be 1")
    if manifest.status != MANIFEST_STATUS:
        errors.append("status must be SKELETON_NOT_EMBEDDED")
    if manifest.embedding_dimensions <= 0:
        errors.append("embedding_dimensions must be positive")
    if manifest.embedding_cache_key_policy != DEFAULT_CACHE_KEY_POLICY:
        errors.append("unexpected embedding_cache_key_policy")
    seen_chunk_ids: set[str] = set()
    seen_cache_keys: set[str] = set()
    for record in manifest.chunks:
        if not record.chunk_id:
            errors.append("chunk record missing chunk_id")
        if record.chunk_id in seen_chunk_ids:
            errors.append(f"duplicate chunk_id: {record.chunk_id}")
        seen_chunk_ids.add(record.chunk_id)
        if not record.embedding_cache_key:
            errors.append(f"chunk {record.chunk_id} missing embedding_cache_key")
        if record.embedding_cache_key in seen_cache_keys:
            errors.append(f"duplicate embedding_cache_key: {record.embedding_cache_key}")
        seen_cache_keys.add(record.embedding_cache_key)
        if not record.vector_record_id.startswith("vec_"):
            errors.append(f"chunk {record.chunk_id} vector_record_id must start with vec_")
    return errors
