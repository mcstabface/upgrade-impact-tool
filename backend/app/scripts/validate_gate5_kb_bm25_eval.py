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
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def query_context_files(query_context_root: Path) -> list[Path]:
    if not query_context_root.exists():
        return []
    return sorted(query_context_root.glob("*.query_context.json"), key=lambda path: path.stat().st_mtime, reverse=True)


def context_ranker(context: dict[str, Any]) -> str:
    diagnostics = context.get("diagnostics", {}) if isinstance(context.get("diagnostics"), dict) else {}
    return str(diagnostics.get("ranker") or "")


def validate_result_contributions(path: Path, context: dict[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    results = context.get("results")
    if not isinstance(results, list) or not results:
        return [ValidationFailure(check=f"{path.name}.results", detail="Expected non-empty results list.")]

    for index, result in enumerate(results):
        if not isinstance(result, dict):
            failures.append(ValidationFailure(check=f"{path.name}.results[{index}]", detail="Expected result object."))
            continue
        contributions = result.get("term_score_contributions")
        if not isinstance(contributions, dict) or not contributions:
            failures.append(
                ValidationFailure(
                    check=f"{path.name}.results[{index}].term_score_contributions",
                    detail="Expected non-empty term_score_contributions object.",
                )
            )
    return failures


def validate_filtered_results(path: Path, context: dict[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    query = context.get("query", {}) if isinstance(context.get("query"), dict) else {}
    filters = query.get("filters") or {}
    if not isinstance(filters, dict) or not filters:
        return failures

    results = context.get("results", []) if isinstance(context.get("results"), list) else []
    for index, result in enumerate(results):
        if not isinstance(result, dict):
            continue
        for field, expected_value in filters.items():
            if result.get(field) != expected_value:
                failures.append(
                    ValidationFailure(
                        check=f"{path.name}.results[{index}].{field}",
                        detail=f"Filter mismatch: expected {expected_value!r}; found {result.get(field)!r}.",
                    )
                )
    return failures


def validate_context(path: Path, context: dict[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    if context.get("artifact_type") != "kb_chunk_query_context":
        failures.append(
            ValidationFailure(
                check=f"{path.name}.artifact_type",
                detail=f"Expected kb_chunk_query_context; found {context.get('artifact_type')!r}.",
            )
        )
    if context.get("schema_version") != "kb_chunk_query_context.v2":
        failures.append(
            ValidationFailure(
                check=f"{path.name}.schema_version",
                detail=f"Expected kb_chunk_query_context.v2; found {context.get('schema_version')!r}.",
            )
        )

    diagnostics = context.get("diagnostics")
    if not isinstance(diagnostics, dict):
        failures.append(ValidationFailure(check=f"{path.name}.diagnostics", detail="Expected diagnostics object."))
        return failures

    ranker = diagnostics.get("ranker")
    if ranker not in {"tfidf_v1", "bm25_v1"}:
        failures.append(
            ValidationFailure(
                check=f"{path.name}.diagnostics.ranker",
                detail=f"Expected ranker tfidf_v1 or bm25_v1; found {ranker!r}.",
            )
        )

    term_diagnostics = diagnostics.get("term_diagnostics")
    if not isinstance(term_diagnostics, dict) or not term_diagnostics:
        failures.append(
            ValidationFailure(check=f"{path.name}.diagnostics.term_diagnostics", detail="Expected non-empty term diagnostics.")
        )
    else:
        for term, details in term_diagnostics.items():
            if not isinstance(details, dict):
                failures.append(
                    ValidationFailure(check=f"{path.name}.term_diagnostics.{term}", detail="Expected diagnostic object.")
                )
                continue
            for field in ["tfidf_idf", "bm25_idf", "global_posting_count", "filtered_posting_count"]:
                if field not in details:
                    failures.append(
                        ValidationFailure(
                            check=f"{path.name}.term_diagnostics.{term}.{field}",
                            detail="Missing required term diagnostic field.",
                        )
                    )

    ranker_diagnostics = diagnostics.get("ranker_diagnostics")
    if not isinstance(ranker_diagnostics, dict):
        failures.append(
            ValidationFailure(check=f"{path.name}.diagnostics.ranker_diagnostics", detail="Expected ranker diagnostics object.")
        )
    elif ranker == "bm25_v1":
        for field in ["average_document_length", "bm25_k1", "bm25_b", "document_length_field"]:
            if field not in ranker_diagnostics:
                failures.append(
                    ValidationFailure(
                        check=f"{path.name}.diagnostics.ranker_diagnostics.{field}",
                        detail="Missing required BM25 diagnostic field.",
                    )
                )
        if float(ranker_diagnostics.get("average_document_length") or 0) <= 0:
            failures.append(
                ValidationFailure(
                    check=f"{path.name}.diagnostics.ranker_diagnostics.average_document_length",
                    detail="Expected BM25 average document length greater than zero.",
                )
            )

    failures.extend(validate_result_contributions(path, context))
    failures.extend(validate_filtered_results(path, context))
    return failures


def validate(query_context_root: Path, *, min_contexts: int) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    files = query_context_files(query_context_root)
    if len(files) < min_contexts:
        return [
            ValidationFailure(
                check="query_context.count",
                detail=f"Expected at least {min_contexts} query contexts; found {len(files)} under {query_context_root}.",
            )
        ]

    newest = files[:min_contexts]
    saw_tfidf = False
    saw_bm25 = False
    saw_filtered_tfidf = False
    saw_filtered_bm25 = False

    for path in newest:
        context = read_json(path)
        failures.extend(validate_context(path, context))
        ranker = context_ranker(context)
        query = context.get("query", {}) if isinstance(context.get("query"), dict) else {}
        has_filters = bool(query.get("filters"))
        if ranker == "tfidf_v1":
            saw_tfidf = True
            if has_filters:
                saw_filtered_tfidf = True
        if ranker == "bm25_v1":
            saw_bm25 = True
            if has_filters:
                saw_filtered_bm25 = True

    if not saw_tfidf:
        failures.append(ValidationFailure(check="query_context.tfidf", detail="Expected at least one recent TF-IDF query context."))
    if not saw_bm25:
        failures.append(ValidationFailure(check="query_context.bm25", detail="Expected at least one recent BM25 query context."))
    if not saw_filtered_tfidf:
        failures.append(
            ValidationFailure(check="query_context.filtered_tfidf", detail="Expected at least one recent filtered TF-IDF context.")
        )
    if not saw_filtered_bm25:
        failures.append(
            ValidationFailure(check="query_context.filtered_bm25", detail="Expected at least one recent filtered BM25 context.")
        )

    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 5 BM25/TF-IDF retrieval evaluation query contexts.")
    parser.add_argument(
        "--query-context-root",
        type=Path,
        default=root / "kbs" / "query_context",
        help="Directory containing query context artifacts.",
    )
    parser.add_argument(
        "--min-contexts",
        type=int,
        default=4,
        help="Number of newest query contexts to validate.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate(args.query_context_root, min_contexts=args.min_contexts)

    if failures:
        print("[gate5:validate] FAILED")
        for failure in failures:
            print(f"[gate5:validate] {failure.check}: {failure.detail}")
        raise SystemExit(1)

    print("[gate5:validate] OK")
    print(f"[gate5:validate] query_context_root={args.query_context_root}")
    print(f"[gate5:validate] min_contexts={args.min_contexts}")


if __name__ == "__main__":
    main()
