from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path

from app.scripts.build_embedding_manifest_from_chunks import (
    DEFAULT_SOURCE_CHUNK_MANIFEST,
    build_manifest_from_gate2_chunks,
    load_chunks_from_gate2_manifest,
)
from app.scripts.embedding_manifest_skeleton import validate_embedding_manifest_skeleton
from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_OUTPUT = "kbs/retrieval/kb_embedding_manifest.v1.json"


def read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def assert_source_chunk_manifest_exists() -> Path:
    root = repo_root()
    path = root / DEFAULT_SOURCE_CHUNK_MANIFEST
    if not path.exists():
        raise AssertionError(f"Expected Gate 2 chunk manifest to exist: {path}")
    return path


def assert_chunk_discovery_finds_real_chunks(source_manifest: Path) -> None:
    chunks = load_chunks_from_gate2_manifest(source_manifest, limit=5)
    if len(chunks) != 5:
        raise AssertionError(f"Expected to discover 5 chunks with limit=5, got {len(chunks)}")
    for chunk in chunks:
        if not chunk.get("chunk_id"):
            raise AssertionError(f"Discovered chunk missing chunk_id: {chunk}")
        if not chunk.get("chunk_text"):
            raise AssertionError(f"Discovered chunk missing chunk_text: {chunk}")
        if not chunk.get("citation_payload"):
            raise AssertionError(f"Discovered chunk missing citation_payload: {chunk}")


def assert_manifest_build_writes_skeleton(source_manifest: Path) -> None:
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "kb_embedding_manifest.v1.json"
        count = build_manifest_from_gate2_chunks(source_manifest_path=source_manifest, output_path=output, limit=7)
        if count != 7:
            raise AssertionError(f"Expected 7 manifest chunks, got {count}")
        if not output.exists():
            raise AssertionError(f"Expected output manifest to exist: {output}")
        payload = read_json(output)
        if payload.get("status") != "SKELETON_NOT_EMBEDDED":
            raise AssertionError(f"Expected skeleton status, got: {payload.get('status')}")
        if payload.get("source_chunk_manifest") != DEFAULT_SOURCE_CHUNK_MANIFEST:
            raise AssertionError(f"Unexpected source chunk manifest path: {payload.get('source_chunk_manifest')}")
        if payload.get("vector_store", {}).get("path") != "kbs/retrieval/kb_vectors.v1.jsonl":
            raise AssertionError(f"Unexpected vector path: {payload.get('vector_store')}")
        chunks = payload.get("chunks")
        if not isinstance(chunks, list) or len(chunks) != 7:
            raise AssertionError(f"Expected 7 chunks in written skeleton, got: {chunks}")
        for chunk in chunks:
            if not isinstance(chunk, dict):
                raise AssertionError(f"Expected chunk object, got: {chunk}")
            if not chunk.get("embedding_cache_key"):
                raise AssertionError(f"Expected embedding_cache_key, got: {chunk}")
            if not chunk.get("citation_payload"):
                raise AssertionError(f"Expected citation_payload, got: {chunk}")
            if "vector" in chunk:
                raise AssertionError(f"Skeleton chunk must not contain vector values: {chunk}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 18C source chunk manifest discovery and skeleton build.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    source_manifest = assert_source_chunk_manifest_exists()
    assert_chunk_discovery_finds_real_chunks(source_manifest)
    assert_manifest_build_writes_skeleton(source_manifest)
    print("[gate18c:chunks] OK")
    print("[gate18c:chunks] source_chunk_manifest=discovered")
    print("[gate18c:chunks] real_chunks=normalized")
    print("[gate18c:chunks] skeleton_manifest=written")
    print("[gate18c:chunks] vectors=not_created")


if __name__ == "__main__":
    main()
