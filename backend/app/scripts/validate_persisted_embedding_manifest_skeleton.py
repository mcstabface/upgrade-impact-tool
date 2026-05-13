from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from app.scripts.build_embedding_manifest_from_chunks import DEFAULT_SOURCE_CHUNK_MANIFEST, sha256_file
from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_EMBEDDING_MANIFEST = "kbs/retrieval/kb_embedding_manifest.v1.json"
DEFAULT_VECTOR_PATH = "kbs/retrieval/kb_vectors.v1.jsonl"
DEFAULT_VECTOR_INDEX_PATH = "kbs/retrieval/kb_vector_index.v1.json"


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def validate_persisted_embedding_manifest_skeleton(
    *,
    manifest_path: Path,
    source_chunk_manifest_path: Path,
) -> list[str]:
    errors: list[str] = []
    if not manifest_path.exists():
        return [f"embedding manifest not found: {manifest_path}"]
    if not source_chunk_manifest_path.exists():
        return [f"source chunk manifest not found: {source_chunk_manifest_path}"]

    manifest = read_json(manifest_path)
    source_manifest = read_json(source_chunk_manifest_path)

    if manifest.get("manifest_version") != "1":
        errors.append("manifest_version must be 1")
    if manifest.get("status") != "SKELETON_NOT_EMBEDDED":
        errors.append("status must be SKELETON_NOT_EMBEDDED")
    if manifest.get("source_chunk_manifest") != DEFAULT_SOURCE_CHUNK_MANIFEST:
        errors.append(f"source_chunk_manifest must be {DEFAULT_SOURCE_CHUNK_MANIFEST}")
    if manifest.get("source_chunk_manifest_sha256") != sha256_file(source_chunk_manifest_path):
        errors.append("source_chunk_manifest_sha256 does not match current source chunk manifest")
    if manifest.get("embedding_model") != "text-embedding-3-small":
        errors.append("embedding_model must remain text-embedding-3-small")
    if manifest.get("embedding_dimensions") != 1536:
        errors.append("embedding_dimensions must remain 1536")
    if manifest.get("embedding_input_policy") != "chunk_text_with_stable_metadata_prefix_v1":
        errors.append("embedding_input_policy is not expected value")
    if manifest.get("embedding_cache_key_policy") != "sha256(model|dimensions|input_policy|chunk_id|chunk_text_sha256)":
        errors.append("embedding_cache_key_policy is not expected value")

    vector_store = manifest.get("vector_store")
    if not isinstance(vector_store, dict):
        errors.append("vector_store must be an object")
    else:
        if vector_store.get("path") != DEFAULT_VECTOR_PATH:
            errors.append(f"vector_store.path must be {DEFAULT_VECTOR_PATH}")
        if vector_store.get("index_path") != DEFAULT_VECTOR_INDEX_PATH:
            errors.append(f"vector_store.index_path must be {DEFAULT_VECTOR_INDEX_PATH}")

    chunks = manifest.get("chunks")
    if not isinstance(chunks, list):
        errors.append("chunks must be a list")
        chunks = []

    expected_chunk_count = source_manifest.get("chunk_count")
    if expected_chunk_count is not None and len(chunks) != expected_chunk_count:
        errors.append(f"chunk count mismatch: manifest has {len(chunks)}, source manifest has {expected_chunk_count}")

    seen_chunk_ids: set[str] = set()
    seen_cache_keys: set[str] = set()
    seen_vector_ids: set[str] = set()
    for index, chunk in enumerate(chunks):
        if not isinstance(chunk, dict):
            errors.append(f"chunks[{index}] must be an object")
            continue
        chunk_id = str(chunk.get("chunk_id") or "")
        cache_key = str(chunk.get("embedding_cache_key") or "")
        vector_record_id = str(chunk.get("vector_record_id") or "")
        citation_payload = chunk.get("citation_payload")

        if not chunk_id:
            errors.append(f"chunks[{index}] missing chunk_id")
        if chunk_id in seen_chunk_ids:
            errors.append(f"duplicate chunk_id: {chunk_id}")
        seen_chunk_ids.add(chunk_id)

        if len(str(chunk.get("chunk_text_sha256") or "")) != 64:
            errors.append(f"chunks[{index}] invalid chunk_text_sha256")
        if len(str(chunk.get("embedding_input_sha256") or "")) != 64:
            errors.append(f"chunks[{index}] invalid embedding_input_sha256")
        if len(cache_key) != 64:
            errors.append(f"chunks[{index}] invalid embedding_cache_key")
        if cache_key in seen_cache_keys:
            errors.append(f"duplicate embedding_cache_key: {cache_key}")
        seen_cache_keys.add(cache_key)

        if not vector_record_id.startswith("vec_"):
            errors.append(f"chunks[{index}] vector_record_id must start with vec_")
        if vector_record_id in seen_vector_ids:
            errors.append(f"duplicate vector_record_id: {vector_record_id}")
        seen_vector_ids.add(vector_record_id)

        if not isinstance(citation_payload, dict) or not citation_payload:
            errors.append(f"chunks[{index}] missing citation_payload")
        if "vector" in chunk:
            errors.append(f"chunks[{index}] must not contain vector values")

    root = repo_root()
    if (root / DEFAULT_VECTOR_PATH).exists():
        errors.append(f"vector file must not exist in Gate 18D: {DEFAULT_VECTOR_PATH}")
    if (root / DEFAULT_VECTOR_INDEX_PATH).exists():
        errors.append(f"vector index file must not exist in Gate 18D: {DEFAULT_VECTOR_INDEX_PATH}")
    return errors


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate persisted Gate 18D embedding manifest skeleton.")
    parser.add_argument("--manifest", type=Path, default=root / DEFAULT_EMBEDDING_MANIFEST)
    parser.add_argument("--source-chunk-manifest", type=Path, default=root / DEFAULT_SOURCE_CHUNK_MANIFEST)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    errors = validate_persisted_embedding_manifest_skeleton(
        manifest_path=args.manifest,
        source_chunk_manifest_path=args.source_chunk_manifest,
    )
    if errors:
        print("[gate18d:persist] FAILED")
        for error in errors:
            print(f"[gate18d:persist] {error}")
        raise SystemExit(1)
    print("[gate18d:persist] OK")
    print("[gate18d:persist] full_manifest=written")
    print("[gate18d:persist] source_chunk_hash=validated")
    print("[gate18d:persist] citation_payloads=present")
    print("[gate18d:persist] vectors=not_created")


if __name__ == "__main__":
    main()
