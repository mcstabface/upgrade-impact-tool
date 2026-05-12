from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sqlite3
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.build_kb_chunk_lexical_index import tokenize

SAFE_FILENAME_RE = re.compile(r"[^A-Za-z0-9._-]+")
FILTER_FIELDS = {
    "kb_document_id",
    "maintenance_pack",
    "bug_patch_number",
    "product",
    "category",
}
RankerName = Literal["tfidf", "bm25"]


@dataclass(frozen=True)
class QueryResult:
    rank: int
    chunk_id: str
    score: float
    matched_terms: list[str]
    term_hits: dict[str, int]
    term_score_contributions: dict[str, float]
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


def stable_query_context_id(context: KBChunkQueryContext) -> str:
    identity = {
        "query_text": context.query.get("query_text"),
        "filters": context.query.get("filters") or {},
        "top_k": context.query.get("top_k"),
        "limit_candidates": context.query.get("limit_candidates"),
        "max_chunks_per_child_pdf": context.query.get("max_chunks_per_child_pdf"),
        "max_chunks_per_bug_patch": context.query.get("max_chunks_per_bug_patch"),
        "ranker": context.diagnostics.get("ranker"),
        "schema_version": context.schema_version,
    }
    payload = json.dumps(identity, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def connect(index_path: Path) -> sqlite3.Connection:
    if not index_path.exists():
        raise FileNotFoundError(f"Lexical index not found: {index_path}")
    conn = sqlite3.connect(index_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_index_metadata(conn: sqlite3.Connection) -> dict[str, str]:
    rows = conn.execute("SELECT key, value FROM metadata ORDER BY key").fetchall()
    return {row["key"]: row["value"] for row in rows}


def clean_filters(raw_filters: dict[str, str | None]) -> dict[str, str]:
    filters: dict[str, str] = {}
    for key, value in raw_filters.items():
        if key not in FILTER_FIELDS:
            raise ValueError(f"Unsupported query filter: {key}")
        if value is None:
            continue
        text = str(value).strip()
        if text:
            filters[key] = text
    return filters


def build_filter_clause(filters: dict[str, str], *, table_alias: str | None = None) -> tuple[str, list[str]]:
    if not filters:
        return "", []
    prefix = f"{table_alias}." if table_alias else ""
    clauses = [f"{prefix}{field} = ?" for field in sorted(filters)]
    values = [filters[field] for field in sorted(filters)]
    return " AND " + " AND ".join(clauses), values


def corpus_stats(conn: sqlite3.Connection) -> dict[str, float]:
    row = conn.execute(
        """
        SELECT
            COUNT(*) AS chunk_count,
            AVG(token_count) AS average_document_length
        FROM chunks
        """
    ).fetchone()
    return {
        "chunk_count": float(row["chunk_count"] or 0),
        "average_document_length": float(row["average_document_length"] or 0.0),
    }


def bm25_idf(total_chunks: int, document_frequency: int) -> float:
    return math.log(1.0 + ((total_chunks - document_frequency + 0.5) / (document_frequency + 0.5)))


def tfidf_idf(total_chunks: int, document_frequency: int) -> float:
    return math.log((1 + total_chunks) / (1 + document_frequency)) + 1.0 if total_chunks else 0.0


def fetch_term_diagnostics(conn: sqlite3.Connection, terms: list[str], *, limit_candidates: int, filters: dict[str, str]) -> dict[str, Any]:
    total_chunks = int(conn.execute("SELECT COUNT(*) AS count FROM chunks").fetchone()["count"] or 0)
    filter_clause, filter_values = build_filter_clause(filters, table_alias="c")
    diagnostics: dict[str, Any] = {}

    for term in sorted(set(terms)):
        global_row = conn.execute(
            "SELECT COUNT(*) AS posting_count FROM postings WHERE term = ?",
            (term,),
        ).fetchone()
        filtered_row = conn.execute(
            f"""
            SELECT COUNT(*) AS posting_count
            FROM postings p
            JOIN chunks c ON c.chunk_id = p.chunk_id
            WHERE p.term = ?{filter_clause}
            """,
            (term, *filter_values),
        ).fetchone()
        global_postings = int(global_row["posting_count"] or 0)
        filtered_postings = int(filtered_row["posting_count"] or 0)
        diagnostics[term] = {
            "global_posting_count": global_postings,
            "filtered_posting_count": filtered_postings,
            "idf": round(tfidf_idf(total_chunks, global_postings), 6),
            "tfidf_idf": round(tfidf_idf(total_chunks, global_postings), 6),
            "bm25_idf": round(bm25_idf(total_chunks, global_postings), 6) if total_chunks else 0.0,
            "candidate_limit": limit_candidates,
            "candidate_limited": filtered_postings > limit_candidates,
        }
    return diagnostics


def fetch_candidate_chunk_ids(
    conn: sqlite3.Connection,
    terms: list[str],
    *,
    limit_candidates: int,
    filters: dict[str, str],
) -> dict[str, dict[str, int]]:
    candidates: dict[str, dict[str, int]] = {}
    filter_clause, filter_values = build_filter_clause(filters, table_alias="c")
    for term in sorted(set(terms)):
        rows = conn.execute(
            f"""
            SELECT p.chunk_id, p.term_count
            FROM postings p
            JOIN chunks c ON c.chunk_id = p.chunk_id
            WHERE p.term = ?{filter_clause}
            ORDER BY p.chunk_id
            LIMIT ?
            """,
            (term, *filter_values, limit_candidates),
        ).fetchall()
        for row in rows:
            chunk_terms = candidates.setdefault(row["chunk_id"], {})
            chunk_terms[term] = int(row["term_count"])
    return candidates


def fetch_chunk_rows(conn: sqlite3.Connection, chunk_ids: list[str]) -> dict[str, sqlite3.Row]:
    if not chunk_ids:
        return {}
    placeholders = ",".join("?" for _ in chunk_ids)
    rows = conn.execute(
        f"SELECT * FROM chunks WHERE chunk_id IN ({placeholders})",
        chunk_ids,
    ).fetchall()
    return {row["chunk_id"]: row for row in rows}


def score_candidates_tfidf(
    *,
    total_chunks: int,
    candidates: dict[str, dict[str, int]],
    query_terms: list[str],
    document_frequency_by_term: dict[str, int],
) -> list[tuple[str, float, dict[str, int], dict[str, float]]]:
    query_counts = Counter(query_terms)
    scored: list[tuple[str, float, dict[str, int], dict[str, float]]] = []
    idf_cache = {
        term: tfidf_idf(total_chunks, document_frequency_by_term.get(term, 0))
        for term in set(query_terms)
    }

    for chunk_id, term_hits in candidates.items():
        score = 0.0
        contributions: dict[str, float] = {}
        for term, query_count in query_counts.items():
            hit_count = term_hits.get(term, 0)
            if hit_count <= 0:
                continue
            contribution = float(query_count) * float(hit_count) * idf_cache[term]
            contributions[term] = round(contribution, 6)
            score += contribution
        scored.append((chunk_id, score, term_hits, contributions))

    return sorted(scored, key=lambda item: (-item[1], item[0]))


def score_candidates_bm25(
    *,
    total_chunks: int,
    average_document_length: float,
    candidates: dict[str, dict[str, int]],
    query_terms: list[str],
    document_frequency_by_term: dict[str, int],
    chunk_rows: dict[str, sqlite3.Row],
    k1: float,
    b: float,
) -> list[tuple[str, float, dict[str, int], dict[str, float]]]:
    query_counts = Counter(query_terms)
    scored: list[tuple[str, float, dict[str, int], dict[str, float]]] = []
    idf_cache = {
        term: bm25_idf(total_chunks, document_frequency_by_term.get(term, 0))
        for term in set(query_terms)
    }

    safe_avgdl = average_document_length if average_document_length > 0 else 1.0
    for chunk_id, term_hits in candidates.items():
        row = chunk_rows.get(chunk_id)
        if row is None:
            continue
        document_length = float(row["token_count"] or 0.0)
        length_norm = k1 * (1.0 - b + b * (document_length / safe_avgdl))
        score = 0.0
        contributions: dict[str, float] = {}
        for term, query_count in query_counts.items():
            term_frequency = float(term_hits.get(term, 0))
            if term_frequency <= 0:
                continue
            tf_component = ((term_frequency * (k1 + 1.0)) / (term_frequency + length_norm))
            contribution = float(query_count) * idf_cache[term] * tf_component
            contributions[term] = round(contribution, 6)
            score += contribution
        scored.append((chunk_id, score, term_hits, contributions))

    return sorted(scored, key=lambda item: (-item[1], item[0]))


def score_candidates(
    conn: sqlite3.Connection,
    candidates: dict[str, dict[str, int]],
    query_terms: list[str],
    *,
    ranker: RankerName,
    bm25_k1: float,
    bm25_b: float,
) -> tuple[list[tuple[str, float, dict[str, int], dict[str, float]]], dict[str, sqlite3.Row], dict[str, Any]]:
    if not candidates:
        return [], {}, {}

    stats = corpus_stats(conn)
    total_chunks = int(stats["chunk_count"] or 1)
    document_frequency_by_term = {
        term: int(
            conn.execute(
                "SELECT COUNT(*) AS count FROM postings WHERE term = ?",
                (term,),
            ).fetchone()["count"]
            or 0
        )
        for term in sorted(set(query_terms))
    }
    chunk_rows = fetch_chunk_rows(conn, list(candidates))

    if ranker == "bm25":
        scored = score_candidates_bm25(
            total_chunks=total_chunks,
            average_document_length=float(stats["average_document_length"] or 0.0),
            candidates=candidates,
            query_terms=query_terms,
            document_frequency_by_term=document_frequency_by_term,
            chunk_rows=chunk_rows,
            k1=bm25_k1,
            b=bm25_b,
        )
        ranker_diagnostics = {
            "ranker": "bm25_v1",
            "bm25_k1": bm25_k1,
            "bm25_b": bm25_b,
            "average_document_length": round(float(stats["average_document_length"] or 0.0), 6),
            "document_length_field": "chunks.token_count",
        }
    else:
        scored = score_candidates_tfidf(
            total_chunks=total_chunks,
            candidates=candidates,
            query_terms=query_terms,
            document_frequency_by_term=document_frequency_by_term,
        )
        ranker_diagnostics = {
            "ranker": "tfidf_v1",
        }

    return scored, chunk_rows, ranker_diagnostics


def apply_source_diversity(
    scored: list[tuple[str, float, dict[str, int], dict[str, float]]],
    chunk_rows: dict[str, sqlite3.Row],
    *,
    max_chunks_per_child_pdf: int | None,
    max_chunks_per_bug_patch: int | None,
) -> tuple[list[tuple[str, float, dict[str, int], dict[str, float]]], dict[str, Any]]:
    kept: list[tuple[str, float, dict[str, int], dict[str, float]]] = []
    child_pdf_counts: defaultdict[str, int] = defaultdict(int)
    bug_patch_counts: defaultdict[str, int] = defaultdict(int)
    excluded_by_reason: Counter[str] = Counter()

    for item in scored:
        chunk_id = item[0]
        row = chunk_rows.get(chunk_id)
        if row is None:
            excluded_by_reason["missing_chunk_row"] += 1
            continue

        child_pdf = row["child_pdf_path"] or "UNKNOWN_CHILD_PDF"
        bug_patch = row["bug_patch_number"] or "UNKNOWN_BUG_PATCH"

        if max_chunks_per_child_pdf is not None and child_pdf_counts[child_pdf] >= max_chunks_per_child_pdf:
            excluded_by_reason["max_chunks_per_child_pdf"] += 1
            continue
        if max_chunks_per_bug_patch is not None and bug_patch_counts[bug_patch] >= max_chunks_per_bug_patch:
            excluded_by_reason["max_chunks_per_bug_patch"] += 1
            continue

        kept.append(item)
        child_pdf_counts[child_pdf] += 1
        bug_patch_counts[bug_patch] += 1

    return kept, {
        "enabled": max_chunks_per_child_pdf is not None or max_chunks_per_bug_patch is not None,
        "max_chunks_per_child_pdf": max_chunks_per_child_pdf,
        "max_chunks_per_bug_patch": max_chunks_per_bug_patch,
        "excluded_by_reason": dict(sorted(excluded_by_reason.items())),
    }


def query_index(
    index_path: Path,
    query_text: str,
    *,
    top_k: int,
    limit_candidates: int,
    filters: dict[str, str] | None = None,
    max_chunks_per_child_pdf: int | None = None,
    max_chunks_per_bug_patch: int | None = None,
    ranker: RankerName = "tfidf",
    bm25_k1: float = 1.2,
    bm25_b: float = 0.75,
) -> KBChunkQueryContext:
    query_terms = tokenize(query_text)
    query_id = stable_query_id(query_text)
    generated_utc = datetime.now(timezone.utc).isoformat()
    active_filters = clean_filters(filters or {})

    with connect(index_path) as conn:
        index_metadata = fetch_index_metadata(conn)
        term_diagnostics = fetch_term_diagnostics(
            conn,
            query_terms,
            limit_candidates=limit_candidates,
            filters=active_filters,
        )
        candidates = fetch_candidate_chunk_ids(
            conn,
            query_terms,
            limit_candidates=limit_candidates,
            filters=active_filters,
        )
        scored, scored_chunk_rows, ranker_diagnostics = score_candidates(
            conn,
            candidates,
            query_terms,
            ranker=ranker,
            bm25_k1=bm25_k1,
            bm25_b=bm25_b,
        )
        diverse_scored, diversity_diagnostics = apply_source_diversity(
            scored,
            scored_chunk_rows,
            max_chunks_per_child_pdf=max_chunks_per_child_pdf,
            max_chunks_per_bug_patch=max_chunks_per_bug_patch,
        )
        top_scored = diverse_scored[:top_k]
        chunk_rows = {chunk_id: scored_chunk_rows[chunk_id] for chunk_id, _, _, _ in top_scored if chunk_id in scored_chunk_rows}

        results: list[QueryResult] = []
        for rank, (chunk_id, score, term_hits, contributions) in enumerate(top_scored, start=1):
            row = chunk_rows[chunk_id]
            matched_terms = sorted(term for term in term_hits if term_hits[term] > 0)
            results.append(
                QueryResult(
                    rank=rank,
                    chunk_id=chunk_id,
                    score=round(score, 6),
                    matched_terms=matched_terms,
                    term_hits={term: term_hits[term] for term in matched_terms},
                    term_score_contributions={term: contributions[term] for term in matched_terms},
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
        schema_version="kb_chunk_query_context.v2",
        generated_utc=generated_utc,
        query={
            "query_id": query_id,
            "query_text": query_text,
            "query_terms": query_terms,
            "top_k": top_k,
            "limit_candidates": limit_candidates,
            "filters": active_filters,
            "max_chunks_per_child_pdf": max_chunks_per_child_pdf,
            "max_chunks_per_bug_patch": max_chunks_per_bug_patch,
            "ranker": ranker,
            "bm25_k1": bm25_k1,
            "bm25_b": bm25_b,
        },
        index={
            "index_path": str(index_path),
            "metadata": index_metadata,
        },
        diagnostics={
            "query_term_count": len(query_terms),
            "unique_query_term_count": len(set(query_terms)),
            "term_diagnostics": term_diagnostics,
            "candidate_count": len(candidates),
            "scored_count": len(scored),
            "post_diversity_scored_count": len(diverse_scored),
            "returned_count": len(results),
            "ranker": ranker_diagnostics["ranker"],
            "ranker_diagnostics": ranker_diagnostics,
            "sort": "score desc, chunk_id asc",
            "source_diversity": diversity_diagnostics,
        },
        results=results,
    )


def output_path_for_query(output_root: Path, query_text: str) -> Path:
    query_id = stable_query_id(query_text)
    slug = safe_slug(query_text)
    return output_root / f"{slug}__{query_id}.query_context.json"


def output_path_for_context(output_root: Path, context: KBChunkQueryContext) -> Path:
    query_text = str(context.query.get("query_text") or "query")
    query_id = context.query.get("query_id") or stable_query_id(query_text)
    context_id = stable_query_context_id(context)
    slug = safe_slug(query_text)
    return output_root / f"{slug}__{query_id}__{context_id}.query_context.json"


def write_query_context(context: KBChunkQueryContext, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(context), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def print_results(context: KBChunkQueryContext) -> None:
    print(f"Query ID: {context.query['query_id']}")
    print(f"Ranker: {context.diagnostics['ranker']}")
    print(f"Query terms: {', '.join(context.query['query_terms'])}")
    if context.query.get("filters"):
        print(f"Filters: {context.query['filters']}")
    print(f"Candidates: {context.diagnostics['candidate_count']}")
    print(f"Scored after diversity: {context.diagnostics['post_diversity_scored_count']}")
    print(f"Returned: {context.diagnostics['returned_count']}")
    print("Term diagnostics:")
    for term, details in context.diagnostics.get("term_diagnostics", {}).items():
        print(
            f"   {term}: global_postings={details['global_posting_count']} "
            f"filtered_postings={details['filtered_posting_count']} "
            f"tfidf_idf={details['tfidf_idf']} bm25_idf={details['bm25_idf']}"
        )
    for result in context.results:
        print("")
        print(f"#{result.rank} score={result.score} chunk={result.chunk_id}")
        print(f"   KB={result.kb_document_id} MP={result.maintenance_pack} bug={result.bug_patch_number}")
        print(f"   product={result.product}")
        print(f"   category={result.category}")
        print(f"   child_pdf={result.child_pdf_path}")
        print(f"   matched_terms={', '.join(result.matched_terms)}")
        print(f"   term_score_contributions={result.term_score_contributions}")
        snippet = " ".join(result.text.split())[:280]
        print(f"   snippet={snippet}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Query the Gate 3/4/5 KB chunk lexical index.")
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
    parser.add_argument("--ranker", choices=["tfidf", "bm25"], default="tfidf", help="Deterministic ranking model.")
    parser.add_argument("--bm25-k1", type=float, default=1.2, help="BM25 k1 saturation parameter.")
    parser.add_argument("--bm25-b", type=float, default=0.75, help="BM25 length normalization parameter.")
    parser.add_argument("--kb-document-id", help="Filter results to a KB document ID.")
    parser.add_argument("--maintenance-pack", help="Filter results to a maintenance pack label.")
    parser.add_argument("--bug-patch-number", help="Filter results to a bug / patch number.")
    parser.add_argument("--product", help="Filter results to a product.")
    parser.add_argument("--category", help="Filter results to a category.")
    parser.add_argument("--max-chunks-per-child-pdf", type=int, help="Limit returned/scored chunks per child PDF.")
    parser.add_argument("--max-chunks-per-bug-patch", type=int, help="Limit returned/scored chunks per bug / patch number.")
    parser.add_argument("--no-write", action="store_true", help="Do not write a query context artifact.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    filters = clean_filters(
        {
            "kb_document_id": args.kb_document_id,
            "maintenance_pack": args.maintenance_pack,
            "bug_patch_number": args.bug_patch_number,
            "product": args.product,
            "category": args.category,
        }
    )
    context = query_index(
        args.index_path,
        args.query,
        top_k=args.top_k,
        limit_candidates=args.limit_candidates,
        filters=filters,
        max_chunks_per_child_pdf=args.max_chunks_per_child_pdf,
        max_chunks_per_bug_patch=args.max_chunks_per_bug_patch,
        ranker=args.ranker,
        bm25_k1=args.bm25_k1,
        bm25_b=args.bm25_b,
    )
    print_results(context)

    if not args.no_write:
        output_path = output_path_for_context(args.output_root, context)
        write_query_context(context, output_path)
        print("")
        print(f"Wrote KB query context artifact: {output_path}")


if __name__ == "__main__":
    main()
