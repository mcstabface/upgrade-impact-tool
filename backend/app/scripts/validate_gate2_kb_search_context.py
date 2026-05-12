from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


@dataclass(frozen=True)
class ValidationFailure:
    check: str
    detail: str


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required manifest not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def require_int(manifest: dict[str, Any], key: str, failures: list[ValidationFailure], *, manifest_name: str) -> int:
    value = manifest.get(key)
    if not isinstance(value, int):
        failures.append(
            ValidationFailure(
                check=f"{manifest_name}.{key}",
                detail=f"Expected integer field {key!r}; found {value!r}.",
            )
        )
        return 0
    return value


def validate_text_manifest(text_manifest: dict[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []

    matched_row_count = require_int(text_manifest, "matched_row_count", failures, manifest_name="text")
    artifact_count = require_int(text_manifest, "artifact_count", failures, manifest_name="text")
    extraction_failed_count = require_int(text_manifest, "extraction_failed_count", failures, manifest_name="text")

    if artifact_count + extraction_failed_count != matched_row_count:
        failures.append(
            ValidationFailure(
                check="text.artifact_count_plus_failures",
                detail=(
                    "Text extraction invariant failed: "
                    f"artifact_count ({artifact_count}) + extraction_failed_count ({extraction_failed_count}) "
                    f"!= matched_row_count ({matched_row_count})."
                ),
            )
        )

    artifacts = text_manifest.get("artifacts")
    if not isinstance(artifacts, list):
        failures.append(
            ValidationFailure(
                check="text.artifacts",
                detail="Expected text manifest artifacts to be a list.",
            )
        )
        return failures

    if len(artifacts) != artifact_count:
        failures.append(
            ValidationFailure(
                check="text.artifacts_length",
                detail=f"Text manifest artifact list length ({len(artifacts)}) != artifact_count ({artifact_count}).",
            )
        )

    required_artifact_fields = {
        "artifact_path",
        "kb_document_id",
        "maintenance_pack",
        "portfolio_file",
        "child_pdf_path",
        "child_sha256",
        "bug_patch_number",
        "product",
        "category",
        "char_count",
        "page_count",
        "text_sha256",
    }

    for index, artifact in enumerate(artifacts):
        if not isinstance(artifact, dict):
            failures.append(
                ValidationFailure(
                    check=f"text.artifacts[{index}]",
                    detail="Expected artifact record to be an object.",
                )
            )
            continue
        missing = sorted(field for field in required_artifact_fields if field not in artifact)
        if missing:
            failures.append(
                ValidationFailure(
                    check=f"text.artifacts[{index}].required_fields",
                    detail=f"Missing required artifact fields: {', '.join(missing)}.",
                )
            )

    return failures


def validate_chunk_manifest(chunk_manifest: dict[str, Any], *, expected_source_artifact_count: int) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []

    source_artifact_count = require_int(chunk_manifest, "source_artifact_count", failures, manifest_name="chunks")
    chunk_collection_count = require_int(chunk_manifest, "chunk_collection_count", failures, manifest_name="chunks")
    skipped_empty_text_count = require_int(chunk_manifest, "skipped_empty_text_count", failures, manifest_name="chunks")
    failure_count = require_int(chunk_manifest, "failure_count", failures, manifest_name="chunks")
    chunk_count = require_int(chunk_manifest, "chunk_count", failures, manifest_name="chunks")

    if source_artifact_count != expected_source_artifact_count:
        failures.append(
            ValidationFailure(
                check="chunks.source_artifact_count",
                detail=(
                    f"Chunk source_artifact_count ({source_artifact_count}) "
                    f"!= text artifact_count ({expected_source_artifact_count})."
                ),
            )
        )

    if chunk_collection_count + skipped_empty_text_count + failure_count != source_artifact_count:
        failures.append(
            ValidationFailure(
                check="chunks.collection_skip_failure_sum",
                detail=(
                    "Chunking invariant failed: "
                    f"chunk_collection_count ({chunk_collection_count}) + "
                    f"skipped_empty_text_count ({skipped_empty_text_count}) + "
                    f"failure_count ({failure_count}) != source_artifact_count ({source_artifact_count})."
                ),
            )
        )

    if chunk_collection_count > 0 and chunk_count <= 0:
        failures.append(
            ValidationFailure(
                check="chunks.chunk_count",
                detail="Chunk manifest has chunk collections but zero chunks.",
            )
        )

    collections = chunk_manifest.get("collections")
    if not isinstance(collections, list):
        failures.append(
            ValidationFailure(
                check="chunks.collections",
                detail="Expected chunk manifest collections to be a list.",
            )
        )
        return failures

    if len(collections) != chunk_collection_count:
        failures.append(
            ValidationFailure(
                check="chunks.collections_length",
                detail=(
                    f"Chunk manifest collections length ({len(collections)}) "
                    f"!= chunk_collection_count ({chunk_collection_count})."
                ),
            )
        )

    required_collection_fields = {
        "collection_path",
        "source_artifact_path",
        "kb_document_id",
        "maintenance_pack",
        "portfolio_file",
        "child_pdf_path",
        "child_sha256",
        "bug_patch_number",
        "product",
        "category",
        "source_char_count",
        "chunk_count",
        "first_chunk_id",
        "last_chunk_id",
    }

    for index, collection in enumerate(collections):
        if not isinstance(collection, dict):
            failures.append(
                ValidationFailure(
                    check=f"chunks.collections[{index}]",
                    detail="Expected collection record to be an object.",
                )
            )
            continue
        missing = sorted(field for field in required_collection_fields if field not in collection)
        if missing:
            failures.append(
                ValidationFailure(
                    check=f"chunks.collections[{index}].required_fields",
                    detail=f"Missing required collection fields: {', '.join(missing)}.",
                )
            )
        if collection.get("chunk_count", 0) <= 0:
            failures.append(
                ValidationFailure(
                    check=f"chunks.collections[{index}].chunk_count",
                    detail="Collection has non-positive chunk_count.",
                )
            )
        first_chunk_id = collection.get("first_chunk_id")
        kb_id = collection.get("kb_document_id")
        bug_patch_number = collection.get("bug_patch_number")
        child_sha256 = collection.get("child_sha256")
        if isinstance(first_chunk_id, str) and kb_id and bug_patch_number and child_sha256:
            expected_prefix = f"{kb_id}::{bug_patch_number}::{child_sha256}::"
            if not first_chunk_id.startswith(expected_prefix):
                failures.append(
                    ValidationFailure(
                        check=f"chunks.collections[{index}].first_chunk_id",
                        detail=(
                            "First chunk ID does not preserve deterministic lineage prefix: "
                            f"expected prefix {expected_prefix!r}, found {first_chunk_id!r}."
                        ),
                    )
                )

    return failures


def validate(text_manifest_path: Path, chunk_manifest_path: Path) -> list[ValidationFailure]:
    text_manifest = read_json(text_manifest_path)
    chunk_manifest = read_json(chunk_manifest_path)

    failures = validate_text_manifest(text_manifest)
    text_artifact_count = text_manifest.get("artifact_count") if isinstance(text_manifest.get("artifact_count"), int) else 0
    failures.extend(validate_chunk_manifest(chunk_manifest, expected_source_artifact_count=text_artifact_count))
    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Validate Gate 2 KB search-context and chunk manifests."
    )
    parser.add_argument(
        "--text-manifest",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_search_context_manifest.json",
        help="Path to kb_search_context_manifest.json.",
    )
    parser.add_argument(
        "--chunk-manifest",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_search_context_chunks_manifest.json",
        help="Path to kb_search_context_chunks_manifest.json.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate(args.text_manifest, args.chunk_manifest)

    if failures:
        print("[gate2:validate] FAILED")
        for failure in failures:
            print(f"[gate2:validate] {failure.check}: {failure.detail}")
        raise SystemExit(1)

    print("[gate2:validate] OK")
    print(f"[gate2:validate] text_manifest={args.text_manifest}")
    print(f"[gate2:validate] chunk_manifest={args.chunk_manifest}")


if __name__ == "__main__":
    main()
