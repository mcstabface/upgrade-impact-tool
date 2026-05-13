from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from app.scripts.embedding_manifest_skeleton import (
    DEFAULT_EMBEDDING_DIMENSIONS,
    DEFAULT_EMBEDDING_MODEL,
    build_chunk_record,
    build_embedding_cache_key,
    build_embedding_manifest_skeleton,
    sha256_text,
    validate_embedding_manifest_skeleton,
    write_embedding_manifest_skeleton,
)
from app.scripts.extract_kb_source_manifest import repo_root


FIXTURE_CHUNK = {
    "chunk_id": "chunk_gate18b_001",
    "source_id": "source_gate18b_pfds",
    "source_path": "kbs/search/fixture_source.txt",
    "source_span": {"start": 0, "end": 42},
    "chunk_text": "Fixture chunk text for embedding manifest skeleton validation.",
    "citation_payload": {"evidence_id": "evidence_gate18b_001"},
}


def assert_cache_key_is_stable() -> None:
    record_one = build_chunk_record(FIXTURE_CHUNK)
    record_two = build_chunk_record(dict(FIXTURE_CHUNK))
    if record_one.embedding_cache_key != record_two.embedding_cache_key:
        raise AssertionError("Expected stable embedding cache key for identical chunk input.")
    if record_one.embedding_input_sha256 != record_two.embedding_input_sha256:
        raise AssertionError("Expected stable embedding input hash for identical chunk input.")


def assert_cache_key_invalidates_on_text_model_and_dimensions() -> None:
    base = build_chunk_record(FIXTURE_CHUNK)
    changed_text = dict(FIXTURE_CHUNK)
    changed_text["chunk_text"] = "Changed fixture chunk text."
    changed_text_record = build_chunk_record(changed_text)
    if base.embedding_cache_key == changed_text_record.embedding_cache_key:
        raise AssertionError("Changing chunk text must change embedding cache key.")

    chunk_text_hash = sha256_text(str(FIXTURE_CHUNK["chunk_text"]))
    changed_model_key = build_embedding_cache_key(
        model="different-model",
        dimensions=DEFAULT_EMBEDDING_DIMENSIONS,
        input_policy="chunk_text_with_stable_metadata_prefix_v1",
        chunk_id=str(FIXTURE_CHUNK["chunk_id"]),
        chunk_text_sha256=chunk_text_hash,
    )
    if base.embedding_cache_key == changed_model_key:
        raise AssertionError("Changing model must change embedding cache key.")

    changed_dimension_key = build_embedding_cache_key(
        model=DEFAULT_EMBEDDING_MODEL,
        dimensions=3072,
        input_policy="chunk_text_with_stable_metadata_prefix_v1",
        chunk_id=str(FIXTURE_CHUNK["chunk_id"]),
        chunk_text_sha256=chunk_text_hash,
    )
    if base.embedding_cache_key == changed_dimension_key:
        raise AssertionError("Changing dimensions must change embedding cache key.")


def assert_manifest_skeleton_validates_and_writes() -> None:
    manifest = build_embedding_manifest_skeleton(
        source_chunk_manifest="kbs/search/kb_search_chunks.v1.json",
        source_chunk_manifest_sha256="fixture-source-manifest-sha256",
        chunks=[FIXTURE_CHUNK],
    )
    errors = validate_embedding_manifest_skeleton(manifest)
    if errors:
        raise AssertionError(f"Expected valid manifest skeleton, got errors: {errors}")
    if manifest.status != "SKELETON_NOT_EMBEDDED":
        raise AssertionError(f"Expected skeleton status, got: {manifest.status}")
    if manifest.chunks[0].vector_record_id == "":
        raise AssertionError("Expected deterministic vector_record_id placeholder.")

    with tempfile.TemporaryDirectory() as temp_dir:
        path = Path(temp_dir) / "kb_embedding_manifest.v1.json"
        write_embedding_manifest_skeleton(path, manifest)
        if not path.exists():
            raise AssertionError("Expected manifest skeleton file to be written.")
        if "SKELETON_NOT_EMBEDDED" not in path.read_text(encoding="utf-8"):
            raise AssertionError("Expected written manifest to preserve skeleton status.")


def assert_duplicate_chunk_id_fails_validation() -> None:
    duplicate = dict(FIXTURE_CHUNK)
    duplicate["chunk_text"] = "Different text but same chunk id."
    manifest = build_embedding_manifest_skeleton(
        source_chunk_manifest="kbs/search/kb_search_chunks.v1.json",
        source_chunk_manifest_sha256="fixture-source-manifest-sha256",
        chunks=[FIXTURE_CHUNK, duplicate],
    )
    errors = validate_embedding_manifest_skeleton(manifest)
    if not any("duplicate chunk_id" in error for error in errors):
        raise AssertionError(f"Expected duplicate chunk_id validation error, got: {errors}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 18B embedding manifest skeleton.")
    parser.add_argument("--repo-root", type=Path, default=root)
    return parser.parse_args()


def main() -> None:
    _ = parse_args()
    assert_cache_key_is_stable()
    assert_cache_key_invalidates_on_text_model_and_dimensions()
    assert_manifest_skeleton_validates_and_writes()
    assert_duplicate_chunk_id_fails_validation()
    print("[gate18b:manifest] OK")
    print("[gate18b:manifest] cache_key=stable")
    print("[gate18b:manifest] invalidation=text_model_dimensions")
    print("[gate18b:manifest] manifest_skeleton=valid")
    print("[gate18b:manifest] embedding_calls=forbidden")


if __name__ == "__main__":
    main()
