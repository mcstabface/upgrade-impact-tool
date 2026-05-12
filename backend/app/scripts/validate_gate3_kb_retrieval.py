from __future__ import annotations

import argparse
import json
import sqlite3
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
        raise FileNotFoundError(f"Required file not found: {path}")
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


def validate_required_tables(conn: sqlite3.Connection) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    expected_tables = {"metadata", "chunks", "postings"}
    rows = conn.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    actual_tables = {row[0] for row in rows}
    missing = sorted(expected_tables - actual_tables)
    if missing:
        failures.append(
            ValidationFailure(
                check="index.required_tables",
                detail=f"Missing required SQLite tables: {', '.join(missing)}.",
            )
        )
    return failures


def validate_index_manifest(index_manifest: dict[str, Any], chunk_manifest: dict[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []

    collection_count = require_int(index_manifest, "collection_count", failures, manifest_name="index")
    indexed_collection_count = require_int(index_manifest, "indexed_collection_count", failures, manifest_name="index")
    chunk_count = require_int(index_manifest, "chunk_count", failures, manifest_name="index")
    indexed_chunk_count = require_int(index_manifest, "indexed_chunk_count", failures, manifest_name="index")
    posting_count = require_int(index_manifest, "posting_count", failures, manifest_name="index")
    vocabulary_size = require_int(index_manifest, "vocabulary_size", failures, manifest_name="index")

    expected_collection_count = require_int(chunk_manifest, "chunk_collection_count", failures, manifest_name="chunks")
    expected_chunk_count = require_int(chunk_manifest, "chunk_count", failures, manifest_name="chunks")

    if collection_count != expected_collection_count:
        failures.append(
            ValidationFailure(
                check="index.collection_count",
                detail=f"Index collection_count ({collection_count}) != Gate 2 chunk_collection_count ({expected_collection_count}).",
            )
        )
    if indexed_collection_count != expected_collection_count:
        failures.append(
            ValidationFailure(
                check="index.indexed_collection_count",
                detail=(
                    f"Index indexed_collection_count ({indexed_collection_count}) "
                    f"!= Gate 2 chunk_collection_count ({expected_collection_count})."
                ),
            )
        )
    if chunk_count != expected_chunk_count:
        failures.append(
            ValidationFailure(
                check="index.chunk_count",
                detail=f"Index chunk_count ({chunk_count}) != Gate 2 chunk_count ({expected_chunk_count}).",
            )
        )
    if indexed_chunk_count != expected_chunk_count:
        failures.append(
            ValidationFailure(
                check="index.indexed_chunk_count",
                detail=f"Index indexed_chunk_count ({indexed_chunk_count}) != Gate 2 chunk_count ({expected_chunk_count}).",
            )
        )
    if posting_count <= 0:
        failures.append(
            ValidationFailure(check="index.posting_count", detail="posting_count must be greater than zero.")
        )
    if vocabulary_size <= 0:
        failures.append(
            ValidationFailure(check="index.vocabulary_size", detail="vocabulary_size must be greater than zero.")
        )

    failures_list = index_manifest.get("failures", [])
    if failures_list:
        failures.append(
            ValidationFailure(
                check="index.failures",
                detail=f"Index manifest reports {len(failures_list)} failure(s).",
            )
        )

    return failures


def validate_sqlite_index(index_path: Path, index_manifest: dict[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    if not index_path.exists():
        return [ValidationFailure(check="index.exists", detail=f"SQLite index does not exist: {index_path}")]

    with sqlite3.connect(index_path) as conn:
        failures.extend(validate_required_tables(conn))
        if failures:
            return failures

        db_chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
        db_posting_count = conn.execute("SELECT COUNT(*) FROM postings").fetchone()[0]
        db_vocabulary_size = conn.execute("SELECT COUNT(DISTINCT term) FROM postings").fetchone()[0]
        db_metadata_count = conn.execute("SELECT COUNT(*) FROM metadata").fetchone()[0]

    manifest_indexed_chunk_count = int(index_manifest.get("indexed_chunk_count") or 0)
    manifest_posting_count = int(index_manifest.get("posting_count") or 0)
    manifest_vocabulary_size = int(index_manifest.get("vocabulary_size") or 0)

    if db_chunk_count != manifest_indexed_chunk_count:
        failures.append(
            ValidationFailure(
                check="sqlite.chunks_count",
                detail=f"SQLite chunks count ({db_chunk_count}) != manifest indexed_chunk_count ({manifest_indexed_chunk_count}).",
            )
        )
    if db_posting_count != manifest_posting_count:
        failures.append(
            ValidationFailure(
                check="sqlite.postings_count",
                detail=f"SQLite postings count ({db_posting_count}) != manifest posting_count ({manifest_posting_count}).",
            )
        )
    if db_vocabulary_size != manifest_vocabulary_size:
        failures.append(
            ValidationFailure(
                check="sqlite.vocabulary_size",
                detail=f"SQLite vocabulary size ({db_vocabulary_size}) != manifest vocabulary_size ({manifest_vocabulary_size}).",
            )
        )
    if db_metadata_count <= 0:
        failures.append(
            ValidationFailure(check="sqlite.metadata", detail="SQLite metadata table must contain at least one row.")
        )

    return failures


def validate_query_contexts(query_context_root: Path, *, require_query_context: bool) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    if not require_query_context:
        return failures

    if not query_context_root.exists():
        return [
            ValidationFailure(
                check="query_context.exists",
                detail=f"Query context directory does not exist: {query_context_root}",
            )
        ]

    artifacts = sorted(query_context_root.glob("*.query_context.json"))
    if not artifacts:
        return [
            ValidationFailure(
                check="query_context.artifacts",
                detail=f"No query context artifacts found under {query_context_root}.",
            )
        ]

    latest = max(artifacts, key=lambda path: path.stat().st_mtime)
    context = read_json(latest)
    if context.get("artifact_type") != "kb_chunk_query_context":
        failures.append(
            ValidationFailure(
                check="query_context.artifact_type",
                detail=f"Latest query context has unexpected artifact_type: {context.get('artifact_type')!r}.",
            )
        )
    returned_count = context.get("diagnostics", {}).get("returned_count")
    if not isinstance(returned_count, int) or returned_count <= 0:
        failures.append(
            ValidationFailure(
                check="query_context.returned_count",
                detail=f"Latest query context returned_count must be greater than zero; found {returned_count!r}.",
            )
        )

    return failures


def validate(
    *,
    chunk_manifest_path: Path,
    index_manifest_path: Path,
    index_path: Path,
    query_context_root: Path,
    require_query_context: bool,
) -> list[ValidationFailure]:
    chunk_manifest = read_json(chunk_manifest_path)
    index_manifest = read_json(index_manifest_path)

    failures = validate_index_manifest(index_manifest, chunk_manifest)
    failures.extend(validate_sqlite_index(index_path, index_manifest))
    failures.extend(validate_query_contexts(query_context_root, require_query_context=require_query_context))
    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 3 KB PFDS retrieval index and smoke-query artifacts.")
    parser.add_argument(
        "--chunk-manifest",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_search_context_chunks_manifest.json",
        help="Path to Gate 2 chunk manifest.",
    )
    parser.add_argument(
        "--index-manifest",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_chunk_lexical_index_manifest.json",
        help="Path to Gate 3 lexical index manifest.",
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=root / "kbs" / "indexes" / "kb_chunk_lexical_index.sqlite",
        help="Path to Gate 3 SQLite lexical index.",
    )
    parser.add_argument(
        "--query-context-root",
        type=Path,
        default=root / "kbs" / "query_context",
        help="Directory containing Gate 3 query context artifacts.",
    )
    parser.add_argument(
        "--skip-query-context-check",
        action="store_true",
        help="Skip query context artifact validation.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate(
        chunk_manifest_path=args.chunk_manifest,
        index_manifest_path=args.index_manifest,
        index_path=args.index_path,
        query_context_root=args.query_context_root,
        require_query_context=not args.skip_query_context_check,
    )

    if failures:
        print("[gate3:validate] FAILED")
        for failure in failures:
            print(f"[gate3:validate] {failure.check}: {failure.detail}")
        raise SystemExit(1)

    print("[gate3:validate] OK")
    print(f"[gate3:validate] chunk_manifest={args.chunk_manifest}")
    print(f"[gate3:validate] index_manifest={args.index_manifest}")
    print(f"[gate3:validate] index_path={args.index_path}")
    if not args.skip_query_context_check:
        print(f"[gate3:validate] query_context_root={args.query_context_root}")


if __name__ == "__main__":
    main()
