from __future__ import annotations

import argparse
import hashlib
import json
import re
import sqlite3
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import relpath, repo_root

TOKEN_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_'-]*")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "by",
    "for",
    "from",
    "has",
    "have",
    "in",
    "into",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "this",
    "to",
    "was",
    "were",
    "with",
}


@dataclass(frozen=True)
class IndexedCollectionRecord:
    collection_path: str
    kb_document_id: str | None
    bug_patch_number: str | None
    product: str | None
    category: str | None
    chunk_count: int
    indexed_chunk_count: int
    token_count: int


@dataclass(frozen=True)
class KBChunkLexicalIndexManifest:
    manifest_type: str
    generated_utc: str
    source_chunk_manifest_path: str
    index_path: str
    collection_count: int
    indexed_collection_count: int
    chunk_count: int
    indexed_chunk_count: int
    posting_count: int
    vocabulary_size: int
    collections: list[IndexedCollectionRecord] = field(default_factory=list)
    failures: list[dict[str, Any]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def tokenize(text: str | None) -> list[str]:
    if not text:
        return []
    tokens = [match.group(0).lower() for match in TOKEN_RE.finditer(text)]
    return [token for token in tokens if len(token) > 1 and token not in STOPWORDS]


def stable_query_id(payload: str) -> str:
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def connect_index(index_path: Path) -> sqlite3.Connection:
    index_path.parent.mkdir(parents=True, exist_ok=True)
    if index_path.exists():
        index_path.unlink()
    conn = sqlite3.connect(index_path)
    conn.execute("PRAGMA journal_mode = WAL")
    conn.execute("PRAGMA synchronous = NORMAL")
    return conn


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        CREATE TABLE metadata (
            key TEXT PRIMARY KEY,
            value TEXT NOT NULL
        );

        CREATE TABLE chunks (
            chunk_id TEXT PRIMARY KEY,
            collection_path TEXT NOT NULL,
            source_artifact_path TEXT NOT NULL,
            kb_document_id TEXT,
            maintenance_pack TEXT,
            bug_patch_number TEXT,
            product TEXT,
            category TEXT,
            portfolio_file TEXT,
            child_pdf_path TEXT,
            child_sha256 TEXT,
            chunk_index INTEGER NOT NULL,
            chunk_count INTEGER NOT NULL,
            start_char INTEGER NOT NULL,
            end_char INTEGER NOT NULL,
            char_count INTEGER NOT NULL,
            token_count INTEGER NOT NULL,
            text_sha256 TEXT NOT NULL,
            text TEXT NOT NULL
        );

        CREATE TABLE postings (
            term TEXT NOT NULL,
            chunk_id TEXT NOT NULL,
            term_count INTEGER NOT NULL,
            PRIMARY KEY (term, chunk_id),
            FOREIGN KEY (chunk_id) REFERENCES chunks(chunk_id)
        );

        CREATE INDEX idx_postings_term ON postings(term);
        CREATE INDEX idx_chunks_kb ON chunks(kb_document_id);
        CREATE INDEX idx_chunks_bug ON chunks(bug_patch_number);
        CREATE INDEX idx_chunks_product ON chunks(product);
        CREATE INDEX idx_chunks_category ON chunks(category);
        """
    )


def insert_metadata(conn: sqlite3.Connection, *, source_chunk_manifest_path: str, generated_utc: str) -> None:
    rows = [
        ("manifest_type", "kb_chunk_lexical_index.v1"),
        ("generated_utc", generated_utc),
        ("source_chunk_manifest_path", source_chunk_manifest_path),
        ("tokenizer", "TOKEN_RE:[A-Za-z0-9][A-Za-z0-9_'-]*; lowercase; len>1; stopwords.v1"),
    ]
    conn.executemany("INSERT INTO metadata(key, value) VALUES (?, ?)", rows)


def index_collection(
    conn: sqlite3.Connection,
    *,
    collection_path: Path,
    collection_relpath: str,
) -> IndexedCollectionRecord:
    collection = read_json(collection_path)
    source_lineage = collection.get("source_lineage", {})
    kb_row = collection.get("kb_row", {})
    chunks = collection.get("chunks", [])

    indexed_chunk_count = 0
    total_token_count = 0
    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        content = chunk.get("content", {})
        position = chunk.get("position", {})
        text = content.get("text") or ""
        tokens = tokenize(text)
        token_counts = Counter(tokens)
        total_token_count += len(tokens)

        if not chunk_id:
            raise ValueError(f"Chunk record in {collection_relpath} is missing chunk_id")

        conn.execute(
            """
            INSERT INTO chunks(
                chunk_id,
                collection_path,
                source_artifact_path,
                kb_document_id,
                maintenance_pack,
                bug_patch_number,
                product,
                category,
                portfolio_file,
                child_pdf_path,
                child_sha256,
                chunk_index,
                chunk_count,
                start_char,
                end_char,
                char_count,
                token_count,
                text_sha256,
                text
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chunk_id,
                collection_relpath,
                collection.get("source_artifact_path"),
                source_lineage.get("kb_document_id"),
                source_lineage.get("maintenance_pack"),
                kb_row.get("bug_patch_number"),
                kb_row.get("product"),
                kb_row.get("category"),
                source_lineage.get("portfolio_file"),
                source_lineage.get("child_pdf_path"),
                source_lineage.get("child_sha256"),
                int(chunk.get("chunk_index") or 0),
                int(chunk.get("chunk_count") or 0),
                int(position.get("start_char") or 0),
                int(position.get("end_char") or 0),
                int(content.get("char_count") or len(text)),
                len(tokens),
                content.get("text_sha256") or hashlib.sha256(text.encode("utf-8")).hexdigest(),
                text,
            ),
        )

        conn.executemany(
            "INSERT INTO postings(term, chunk_id, term_count) VALUES (?, ?, ?)",
            [(term, chunk_id, count) for term, count in sorted(token_counts.items())],
        )
        indexed_chunk_count += 1

    return IndexedCollectionRecord(
        collection_path=collection_relpath,
        kb_document_id=source_lineage.get("kb_document_id"),
        bug_patch_number=kb_row.get("bug_patch_number"),
        product=kb_row.get("product"),
        category=kb_row.get("category"),
        chunk_count=len(chunks),
        indexed_chunk_count=indexed_chunk_count,
        token_count=total_token_count,
    )


def build_index(source_chunk_manifest_path: Path, index_path: Path) -> KBChunkLexicalIndexManifest:
    repository_root = repo_root()
    generated_utc = datetime.now(timezone.utc).isoformat()
    chunk_manifest = read_json(source_chunk_manifest_path)
    collection_records = chunk_manifest.get("collections", [])

    conn = connect_index(index_path)
    failures: list[dict[str, Any]] = []
    indexed: list[IndexedCollectionRecord] = []
    try:
        create_schema(conn)
        insert_metadata(
            conn,
            source_chunk_manifest_path=relpath(source_chunk_manifest_path, repository_root),
            generated_utc=generated_utc,
        )
        with conn:
            for record in collection_records:
                collection_relpath = record.get("collection_path")
                if not collection_relpath:
                    failures.append({"status": "FAILED", "reason": "MISSING_COLLECTION_PATH", "record": record})
                    continue
                collection_path = repository_root / collection_relpath
                if not collection_path.exists():
                    failures.append(
                        {
                            "status": "FAILED",
                            "reason": "COLLECTION_NOT_FOUND",
                            "collection_path": collection_relpath,
                        }
                    )
                    continue
                try:
                    indexed.append(
                        index_collection(
                            conn,
                            collection_path=collection_path,
                            collection_relpath=collection_relpath,
                        )
                    )
                except Exception as exc:  # noqa: BLE001 - preserve per-collection failure.
                    failures.append(
                        {
                            "status": "FAILED",
                            "reason": "COLLECTION_INDEX_FAILED",
                            "collection_path": collection_relpath,
                            "error": str(exc),
                        }
                    )

        posting_count = conn.execute("SELECT COUNT(*) FROM postings").fetchone()[0]
        vocabulary_size = conn.execute("SELECT COUNT(DISTINCT term) FROM postings").fetchone()[0]
        indexed_chunk_count = conn.execute("SELECT COUNT(*) FROM chunks").fetchone()[0]
    finally:
        conn.close()

    warnings: list[str] = []
    if failures:
        warnings.append("One or more chunk collections failed lexical indexing.")

    return KBChunkLexicalIndexManifest(
        manifest_type="kb_chunk_lexical_index_manifest.v1",
        generated_utc=generated_utc,
        source_chunk_manifest_path=relpath(source_chunk_manifest_path, repository_root),
        index_path=relpath(index_path, repository_root),
        collection_count=len(collection_records),
        indexed_collection_count=len(indexed),
        chunk_count=int(chunk_manifest.get("chunk_count") or 0),
        indexed_chunk_count=indexed_chunk_count,
        posting_count=posting_count,
        vocabulary_size=vocabulary_size,
        collections=indexed,
        failures=failures,
        warnings=warnings,
    )


def write_manifest(manifest: KBChunkLexicalIndexManifest, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(manifest), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build a deterministic lexical SQLite index over Gate 2 KB chunks.")
    parser.add_argument(
        "--source-chunk-manifest",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_search_context_chunks_manifest.json",
        help="Path to kb_search_context_chunks_manifest.json.",
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=root / "kbs" / "indexes" / "kb_chunk_lexical_index.sqlite",
        help="SQLite lexical index output path.",
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_chunk_lexical_index_manifest.json",
        help="Lexical index manifest output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    manifest = build_index(args.source_chunk_manifest, args.index_path)
    write_manifest(manifest, args.manifest_output)

    print(f"Wrote KB chunk lexical index: {args.index_path}")
    print(f"Wrote KB chunk lexical index manifest: {args.manifest_output}")
    print(f"Collections: {manifest.collection_count}")
    print(f"Indexed collections: {manifest.indexed_collection_count}")
    print(f"Chunks: {manifest.chunk_count}")
    print(f"Indexed chunks: {manifest.indexed_chunk_count}")
    print(f"Postings: {manifest.posting_count}")
    print(f"Vocabulary size: {manifest.vocabulary_size}")
    print(f"Failures: {len(manifest.failures)}")


if __name__ == "__main__":
    main()
