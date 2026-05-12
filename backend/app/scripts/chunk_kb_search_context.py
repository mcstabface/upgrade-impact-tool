from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import relpath, repo_root

SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")
TOKEN_RE = re.compile(r"\S+")


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    chunk_index: int
    chunk_count: int
    content: dict[str, Any]
    position: dict[str, int]
    lineage: dict[str, Any]


@dataclass(frozen=True)
class ChunkCollectionArtifact:
    artifact_type: str
    schema_version: str
    generated_utc: str
    source_artifact_path: str
    source_lineage: dict[str, Any]
    kb_row: dict[str, Any]
    chunking: dict[str, Any]
    chunks: list[ChunkRecord]


@dataclass(frozen=True)
class KBSearchContextChunksManifest:
    manifest_type: str
    generated_utc: str
    source_manifest_path: str
    output_root: str
    source_artifact_count: int
    chunk_collection_count: int
    chunk_count: int
    skipped_empty_text_count: int
    failure_count: int
    collections: list[dict[str, Any]] = field(default_factory=list)
    skipped: list[dict[str, Any]] = field(default_factory=list)
    failures: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def safe_slug(value: str | None, *, fallback: str) -> str:
    raw = (value or fallback).strip() or fallback
    safe = SAFE_FILENAME_RE.sub("_", raw).strip("._")
    return safe or fallback


def token_estimate(text: str) -> int:
    return len(TOKEN_RE.findall(text))


def normalize_text(text: str | None) -> str:
    if not text:
        return ""
    normalized = text.replace("\r\n", "\n").replace("\r", "\n")
    normalized = re.sub(r"[\t\f\v]+", " ", normalized)
    normalized = re.sub(r"[ \u00a0]+", " ", normalized)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)
    return normalized.strip()


def chunk_ranges(text_length: int, *, target_chars: int, overlap_chars: int) -> list[tuple[int, int]]:
    if text_length <= 0:
        return []
    if target_chars <= 0:
        raise ValueError("target_chars must be greater than zero")
    if overlap_chars < 0:
        raise ValueError("overlap_chars must be zero or greater")
    if overlap_chars >= target_chars:
        raise ValueError("overlap_chars must be smaller than target_chars")

    ranges: list[tuple[int, int]] = []
    start = 0
    while start < text_length:
        end = min(start + target_chars, text_length)
        ranges.append((start, end))
        if end >= text_length:
            break
        start = end - overlap_chars
    return ranges


def build_chunk_id(source_artifact: dict[str, Any], chunk_index: int) -> str:
    lineage = source_artifact.get("source_lineage", {})
    kb_id = lineage.get("kb_document_id") or "UNKNOWN_KB"
    bug_number = source_artifact.get("kb_row", {}).get("bug_patch_number") or "UNKNOWN_FIX"
    child_sha256 = lineage.get("child_sha256") or source_artifact.get("extraction", {}).get("text_sha256") or "NO_HASH"
    return f"{kb_id}::{bug_number}::{child_sha256}::{chunk_index:04d}"


def build_collection(
    *,
    source_artifact: dict[str, Any],
    source_artifact_path: str,
    target_chars: int,
    overlap_chars: int,
) -> ChunkCollectionArtifact:
    text = normalize_text(source_artifact.get("content", {}).get("text"))
    ranges = chunk_ranges(len(text), target_chars=target_chars, overlap_chars=overlap_chars)
    chunk_count = len(ranges)

    chunks: list[ChunkRecord] = []
    for chunk_index, (start, end) in enumerate(ranges):
        chunk_text = text[start:end]
        chunk_id = build_chunk_id(source_artifact, chunk_index)
        chunks.append(
            ChunkRecord(
                chunk_id=chunk_id,
                chunk_index=chunk_index,
                chunk_count=chunk_count,
                content={
                    "text": chunk_text,
                    "char_count": len(chunk_text),
                    "token_estimate": token_estimate(chunk_text),
                    "text_sha256": sha256_text(chunk_text),
                },
                position={
                    "start_char": start,
                    "end_char": end,
                },
                lineage={
                    "kb_document_id": source_artifact.get("source_lineage", {}).get("kb_document_id"),
                    "bug_patch_number": source_artifact.get("kb_row", {}).get("bug_patch_number"),
                    "child_sha256": source_artifact.get("source_lineage", {}).get("child_sha256"),
                    "source_artifact_path": source_artifact_path,
                },
            )
        )

    return ChunkCollectionArtifact(
        artifact_type="kb_source_search_context_chunk_collection",
        schema_version="kb_source_search_context_chunk_collection.v1",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        source_artifact_path=source_artifact_path,
        source_lineage=source_artifact.get("source_lineage", {}),
        kb_row=source_artifact.get("kb_row", {}),
        chunking={
            "strategy": "fixed_chars_with_overlap",
            "target_chars": target_chars,
            "overlap_chars": overlap_chars,
            "source_char_count": len(text),
            "chunk_count": chunk_count,
        },
        chunks=chunks,
    )


def collection_output_path(
    *,
    source_artifact_path: str,
    source_artifact: dict[str, Any],
    output_root: Path,
) -> Path:
    kb_id = safe_slug(source_artifact.get("source_lineage", {}).get("kb_document_id"), fallback="unknown_kb")
    source_stem = safe_slug(Path(source_artifact_path).stem, fallback="source_context")
    return output_root / kb_id / f"{source_stem}__chunks.json"


def build_manifest(
    *,
    source_manifest_path: Path,
    output_root: Path,
    target_chars: int,
    overlap_chars: int,
) -> KBSearchContextChunksManifest:
    repository_root = repo_root()
    source_manifest = read_json(source_manifest_path)
    source_records = source_manifest.get("artifacts", [])

    collections: list[dict[str, Any]] = []
    skipped: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    total_chunks = 0

    for record in source_records:
        source_artifact_path = record.get("artifact_path")
        if not source_artifact_path:
            failures.append({"status": "FAILED", "reason": "MISSING_SOURCE_ARTIFACT_PATH", "record": record})
            continue

        source_path = repository_root / source_artifact_path
        if not source_path.exists():
            failures.append(
                {
                    "status": "FAILED",
                    "reason": "SOURCE_ARTIFACT_NOT_FOUND",
                    "source_artifact_path": source_artifact_path,
                }
            )
            continue

        try:
            source_artifact = read_json(source_path)
            text = normalize_text(source_artifact.get("content", {}).get("text"))
            if not text:
                skipped.append(
                    {
                        "status": "SKIPPED",
                        "reason": "EMPTY_TEXT",
                        "source_artifact_path": source_artifact_path,
                        "kb_document_id": source_artifact.get("source_lineage", {}).get("kb_document_id"),
                        "bug_patch_number": source_artifact.get("kb_row", {}).get("bug_patch_number"),
                    }
                )
                continue

            collection = build_collection(
                source_artifact=source_artifact,
                source_artifact_path=source_artifact_path,
                target_chars=target_chars,
                overlap_chars=overlap_chars,
            )
            output_path = collection_output_path(
                source_artifact_path=source_artifact_path,
                source_artifact=source_artifact,
                output_root=output_root,
            )
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json.dumps(asdict(collection), indent=2, sort_keys=True) + "\n", encoding="utf-8")

            total_chunks += len(collection.chunks)
            collections.append(
                {
                    "collection_path": relpath(output_path, repository_root),
                    "source_artifact_path": source_artifact_path,
                    "kb_document_id": collection.source_lineage.get("kb_document_id"),
                    "maintenance_pack": collection.source_lineage.get("maintenance_pack"),
                    "portfolio_file": collection.source_lineage.get("portfolio_file"),
                    "child_pdf_path": collection.source_lineage.get("child_pdf_path"),
                    "child_sha256": collection.source_lineage.get("child_sha256"),
                    "bug_patch_number": collection.kb_row.get("bug_patch_number"),
                    "product": collection.kb_row.get("product"),
                    "category": collection.kb_row.get("category"),
                    "source_char_count": collection.chunking["source_char_count"],
                    "chunk_count": len(collection.chunks),
                    "first_chunk_id": collection.chunks[0].chunk_id if collection.chunks else None,
                    "last_chunk_id": collection.chunks[-1].chunk_id if collection.chunks else None,
                }
            )
        except Exception as exc:  # noqa: BLE001 - preserve per-artifact failure.
            failures.append(
                {
                    "status": "FAILED",
                    "reason": "CHUNKING_FAILED",
                    "error": str(exc),
                    "source_artifact_path": source_artifact_path,
                }
            )

    warnings: list[str] = []
    if skipped:
        warnings.append("One or more search-context artifacts were skipped because they had no extracted text.")
    if failures:
        warnings.append("One or more search-context artifacts failed chunking.")

    return KBSearchContextChunksManifest(
        manifest_type="kb_search_context_chunks_manifest.v1",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        source_manifest_path=relpath(source_manifest_path, repository_root),
        output_root=relpath(output_root, repository_root),
        source_artifact_count=len(source_records),
        chunk_collection_count=len(collections),
        chunk_count=total_chunks,
        skipped_empty_text_count=len(skipped),
        failure_count=len(failures),
        collections=collections,
        skipped=skipped,
        failures=failures,
        warnings=warnings,
    )


def write_manifest(manifest: KBSearchContextChunksManifest, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(
        description="Chunk Gate 2 KB search-context artifacts into deterministic retrieval units."
    )
    parser.add_argument(
        "--source-manifest",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_search_context_manifest.json",
        help="Path to kb_search_context_manifest.json generated by Gate 2 text extraction.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=root / "kbs" / "search_context_chunks",
        help="Directory where KB search-context chunk collection artifacts should be written.",
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_search_context_chunks_manifest.json",
        help="Gate 2 chunk manifest output path.",
    )
    parser.add_argument(
        "--target-chars",
        type=int,
        default=2000,
        help="Target characters per chunk.",
    )
    parser.add_argument(
        "--overlap-chars",
        type=int,
        default=200,
        help="Overlapping characters between adjacent chunks.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(
        source_manifest_path=args.source_manifest,
        output_root=args.output_root,
        target_chars=args.target_chars,
        overlap_chars=args.overlap_chars,
    )
    write_manifest(manifest, args.manifest_output)

    print(f"Wrote KB search context chunks manifest: {args.manifest_output}")
    print(f"Source search-context artifacts: {manifest.source_artifact_count}")
    print(f"Chunk collections: {manifest.chunk_collection_count}")
    print(f"Chunks: {manifest.chunk_count}")
    print(f"Skipped empty text artifacts: {manifest.skipped_empty_text_count}")
    print(f"Chunking failures: {manifest.failure_count}")


if __name__ == "__main__":
    main()
