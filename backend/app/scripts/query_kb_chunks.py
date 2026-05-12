from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sqlite3
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import relpath, repo_root
from app.scripts.build_kb_chunk_lexical_index import tokenize

SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True)
class QueryResult:
    rank: int
    chunk_id: str
    score: float
    matched_terms: list[str]
    term_hits: dict[str, int]
    kb_document_id: str | None
    maintenance_pack: str | None
    bug_patch_number: str | None
    product: str | None
    category: str | None
    portfolio_file: str | None
    child_pdf_path: str | None
    child_sha256: str | None
    collection_path: str
    source_artifact_path: str
    chunk_index: int
    chunk_count: int
    start_char: int
    end_char: int
    text: str


@dataclass(frozen=True)
class KBChunkQueryContext:
    artifact_type: str
    schema_version: str
    generated_utc: str
    query: dict[str, Any]
    index: dict[str, Any]
    diagnostics: dict[str, Any]
    results: list[QueryResult] = field(default_factory=list)


def safe_slug(value: str, *, fallback: str = "query") -> str:
    raw = value.strip() or fallback
    safe = SAFE_FILENAME_RE.sub("_", raw).strip("._")
    return safe[:80] or fallback


def stable_query_id(query_text: str) -> str:
    return hashlib.sha256(query_text.encode("utf-8")).hexdigest()[:16]


def connect(index_path: Path) -> sqlite3.Connection:
    if not index_path.exists():
        raise FileNotFoundError(f"Lexical index not found: {index_path}")
    conn = sqlite3.connect(index_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_index_metadata(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute("SELECT key, value FROM metadata ORDER BY key").fetchall()
    return {row["key"]: row["value"] for row in rows}


def fetch_candidate_chunk_ids(conn: sqlite3.Connection, terms: list[str], *, limit_candidates: int) -> dict[str, dict[str, int]]:
    candidates: dict[str, dict[str, int]] = {}
    for term in sorted(set(terms)):
        rows = conn.execute(
            """
            SELECT chunk_id, term_count
            FROM postings
            WHERE term = ?
            ORDER BY chunk_id
            LIMIT ?
            """,
            (term, limit_candidates),
        ).fetchall()
        for row in rows:
            chunk_terms = candidates.setdefault(row["chunk_id"], {})
            chunk_terms[term] = int(row["term_count"])
    return candidates


def score_candidates(conn: sqlite3.Connection, candidates: dict[str, dict[str, int]], query_terms: list[str]) -> list[tuple[str, float, dict[str, int]]]:
    if not candidates:
        return []

    total_chunks = conn.execute("SELECT COUNT(*) AS count FROM chunks").fetchone()["count"] or 1
    query_counts = Counter(query_terms)
    scored: list[tuple[str, float, dict[str, int]]] = []

    doc_freq_cache: dict[str, int] = {}
    for term in sorted(set(query_terms)):
        doc_freq_cache[term] = conn.execute(
            "SELECT COUNT(*) AS count FROM postings WHERE term = ?",
            (term,),
        ).fetchone()["count"]

    for chunk_id, term_hits in candidates.items():
        score = 0.0
        for term, query_count in query_counts.items():
            hit_count = term_hits.get(term, 0)
            if hit_count <= 0:
                continue
            doc_freq = doc_freq_cache.get(term, 0)
            idf = math.log((1 + total_chunks) / (1 + doc_freq)) + 1.0
            score += float(query_count) * float(hit_count) * idf
        scored.append((chunk_id, score, term_hits))

    return sorted(scored, key=lambda item: (-item[1], item[0]))


def fetch_chunk_rows(conn: sqlite3.Connection, chunk_ids: list[str]) -> dict[str, sqlite3.Row]:
    if not chunk_ids:
        return {}
    placeholders = ",".join("?" for _ in chunk_ids)
    rows = conn.execute(
        f"SELECT * FROM chunks WHERE chunk_id IN ({placeholders})",
        chunk_ids,
    ).fetchall()
    return {row["chunk_id"]: row for row in rows}


def query_index(index_path: Path, query_text: str, *, top_k: int, limit_candidates: int) -> KBChunkQueryContext:
    query_terms = tokenize(query_text)
    query_id = stable_query_id(query_text)
    generated_utc = datetime.now(timezone.utc).isoformat()

    with connect(index_path) as conn:
        index_metadata = fetch_index_metadata(conn)
        candidates = fetch_candidate_chunk_ids(conn, query_terms, limit_candidates=limit_candidates)
        scored = score_candidates(conn, candidates, query_terms)
        top_scored = scored[:top_k]
        chunk_rows = fetch_chunk_rows(conn, [chunk_id for chunk_id, _, _ in top_scored])

        results: list[QueryResult] = []
        for rank, (chunk_id, score, term_hits) in enumerate(top_scored, start=1):
            row = chunk_rows[chunk_id]
            matched_terms = sorted(term for term in term_hits if term_hits[term] > 0)
            results.append(
                QueryResult(
                    rank=rank,
                    chunk_id=chunk_id,
                    score=round(score, 6),
                    matched_terms=matched_terms,
                    term_hits={term: term_hits[term] for term in matched_terms},
                    kb_document_id=row["kb_document_id"],
                    maintenance_pack=row["maintenance_pack"],
                    bug_patch_number=row["bug_patch_number"],
                    product=row["product"],
                    category=row["category"],
                    portfolio_file=row["portfolio_file"],
                    child_pdf_path=row["child_pdf_path"],
                    child_sha256=row["child_sha256"],
                    collection_path=row["collection_path"],
                    source_artifact_path=row["source_artifact_path"],
                    chunk_index=int(row["chunk_index"]),
                    chunk_count=int(row["chunk_count"]),
                    start_char=int(row["start_char"]),
                    end_char=int(row["end_char"]),
                    text=row["text"],
                )
            )

    return KBChunkQueryContext(
        artifact_type="kb_chunk_query_context",
        schema_version="kb_chunk_query_context.v1",
        generated_utc=generated_utc,
        query={
            "query_id": query_id,
            "query_text": query_text,
            "query_terms": query_terms,
            "top_k": top_k,
            "limit_candidates": limit_candidates,
        },
        index={
            "index_path": str(index_path),
            "metadata": index_metadata,
        },
        diagnostics={
            "query_term_count": len(query_terms),
            "unique_query_term_count": len(set(query_terms)),
            "candidate_count": len(candidates),
            "scored_count": len(scored),
            "returned_count": len(results),
            "ranker": "term_frequency_idf_v1",
            "sort": "score desc, chunk_id asc",
        },
        results=results,
    )


def output_path_for_query(output_root: Path, query_text: str) -> Path:
    query_id = stable_query_id(query_text)
    slug = safe_slug(query_text)
    return output_root / f"{slug}__{query_id}.query_context.json"


def write_query_context(context: KBChunkQueryContext, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(context), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def print_results(context: KBChunkQueryContext) -> None:
    print(f"Query ID: {context.query['query_id']}")
    print(f"Query terms: {', '.join(context.query['query_terms'])}")
    print(f"Candidates: {context.diagnostics['candidate_count']}")
    print(f"Returned: {context.diagnostics['returned_count']}")
    for result in context.results:
        print("")
        print(f"#{result.rank} score={result.score} chunk={result.chunk_id}")
        print(f"   KB={result.kb_document_id} MP={result.maintenance_pack} bug={result.bug_patch_number}")
        print(f"   product={result.product}")
        print(f"   category={result.category}")
        print(f"   child_pdf={result.child_pdf_path}")
        print(f"   matched_terms={', '.join(result.matched_terms)}")
        snippet = " ".join(result.text.split())[:280]
        print(f"   snippet={snippet}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Query the Gate 3 KB chunk lexical index.")
    parser.add_argument("query", help="Query text to search for.")
    parser.add_argument(
        "--index-path",
        type=Path,
        default=root / "kbs" / "indexes" / "kb_chunk_lexical_index.sqlite",
        help="Path to kb_chunk_lexical_index.sqlite.",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        default=root / "kbs" / "query_context",
        help="Directory where query context artifacts should be written.",
    )
    parser.add_argument("--top-k", type=int, default=10, help="Maximum ranked chunks to return.")
    parser.add_argument("--limit-candidates", type=int, default=5000, help="Maximum postings to read per query term.")
    parser.add_argument("--no-write", action="store_true", help="Do not write a query context artifact.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    context = query_index(
        args.index_path,
        args.query,
        top_k=args.top_k,
        limit_candidates=args.limit_candidates,
    )
    print_results(context)

    if not args.no_write:
        output_path = output_path_for_query(args.output_root, args.query)
        write_query_context(context, output_path)
        print("")
        print(f"Wrote KB query context artifact: {output_path}")


if __name__ == "__main__":
    main()
