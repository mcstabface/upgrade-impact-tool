from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from app.scripts.embedding_manifest_skeleton import (
    build_embedding_manifest_skeleton,
    validate_embedding_manifest_skeleton,
    write_embedding_manifest_skeleton,
)
from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_SOURCE_CHUNK_MANIFEST = "kbs/manifests/kb_search_context_chunks_manifest.json"
DEFAULT_EMBEDDING_MANIFEST_OUTPUT = "kbs/retrieval/kb_embedding_manifest.v1.json"


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


def normalize_chunk_record(collection: dict[str, Any], chunk: dict[str, Any]) -> dict[str, Any]:
    content = chunk.get("content") or {}
    if not isinstance(content, dict):
        raise ValueError("chunk.content must be an object")
    lineage = chunk.get("lineage") or {}
    if not isinstance(lineage, dict):
        raise ValueError("chunk.lineage must be an object")
    position = chunk.get("position") or {}
    if not isinstance(position, dict):
        raise ValueError("chunk.position must be an object")

    source_lineage = collection.get("source_lineage") or {}
    kb_row = collection.get("kb_row") or {}
    if not isinstance(source_lineage, dict):
        source_lineage = {}
    if not isinstance(kb_row, dict):
        kb_row = {}

    source_id_parts = [
        str(source_lineage.get("kb_document_id") or lineage.get("kb_document_id") or "UNKNOWN_KB"),
        str(kb_row.get("bug_patch_number") or lineage.get("bug_patch_number") or "UNKNOWN_FIX"),
        str(source_lineage.get("child_sha256") or lineage.get("child_sha256") or "UNKNOWN_CHILD"),
    ]
    source_id = "::".join(source_id_parts)
    source_path = str(lineage.get("source_artifact_path") or collection.get("source_artifact_path") or "")
    return {
        "chunk_id": str(chunk.get("chunk_id") or ""),
        "source_id": source_id,
        "source_path": source_path,
        "source_span": {
            "start": int(position.get("start_char", 0)),
            "end": int(position.get("end_char", 0)),
        },
        "chunk_text": str(content.get("text") or ""),
        "citation_payload": {
            "kb_document_id": source_lineage.get("kb_document_id") or lineage.get("kb_document_id"),
            "bug_patch_number": kb_row.get("bug_patch_number") or lineage.get("bug_patch_number"),
            "product": kb_row.get("product"),
            "category": kb_row.get("category"),
            "portfolio_file": source_lineage.get("portfolio_file"),
            "child_pdf_path": source_lineage.get("child_pdf_path"),
            "child_sha256": source_lineage.get("child_sha256") or lineage.get("child_sha256"),
            "source_artifact_path": source_path,
        },
    }


def load_chunks_from_gate2_manifest(source_manifest_path: Path, *, limit: int | None = None) -> list[dict[str, Any]]:
    root = repo_root()
    manifest = read_json(source_manifest_path)
    collections = manifest.get("collections")
    if not isinstance(collections, list):
        raise ValueError("Gate 2 chunk manifest must contain a collections list")
    chunks: list[dict[str, Any]] = []
    for collection_record in collections:
        if not isinstance(collection_record, dict):
            continue
        collection_path_value = collection_record.get("collection_path")
        if not collection_path_value:
            raise ValueError("collection record missing collection_path")
        collection_path = root / str(collection_path_value)
        collection = read_json(collection_path)
        raw_chunks = collection.get("chunks")
        if not isinstance(raw_chunks, list):
            raise ValueError(f"Chunk collection missing chunks list: {collection_path}")
        for raw_chunk in raw_chunks:
            if not isinstance(raw_chunk, dict):
                raise ValueError(f"Chunk record must be object in {collection_path}")
            chunks.append(normalize_chunk_record(collection, raw_chunk))
            if limit is not None and len(chunks) >= limit:
                return chunks
    return chunks


def build_manifest_from_gate2_chunks(
    *,
    source_manifest_path: Path,
    output_path: Path,
    limit: int | None = None,
) -> int:
    root = repo_root()
    chunks = load_chunks_from_gate2_manifest(source_manifest_path, limit=limit)
    if not chunks:
        raise ValueError("No chunks discovered from source chunk manifest")
    manifest = build_embedding_manifest_skeleton(
        source_chunk_manifest=str(source_manifest_path.relative_to(root)) if source_manifest_path.is_relative_to(root) else str(source_manifest_path),
        source_chunk_manifest_sha256=sha256_file(source_manifest_path),
        chunks=chunks,
    )
    errors = validate_embedding_manifest_skeleton(manifest)
    if errors:
        raise ValueError("Embedding manifest skeleton failed validation: " + "; ".join(errors))
    write_embedding_manifest_skeleton(output_path, manifest)
    return len(manifest.chunks)


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build Gate 18C embedding manifest skeleton from Gate 2 chunk artifacts.")
    parser.add_argument("--source-chunk-manifest", type=Path, default=root / DEFAULT_SOURCE_CHUNK_MANIFEST)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_EMBEDDING_MANIFEST_OUTPUT)
    parser.add_argument("--limit", type=int, default=None, help="Optional chunk limit for smoke validation.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    count = build_manifest_from_gate2_chunks(
        source_manifest_path=args.source_chunk_manifest,
        output_path=args.output,
        limit=args.limit,
    )
    print(f"[gate18c:build] Wrote embedding manifest skeleton: {args.output}")
    print(f"[gate18c:build] chunks={count}")
    print("[gate18c:build] embedding_calls=forbidden")


if __name__ == "__main__":
    main()
