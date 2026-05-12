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


def validate_context(path: Path, context: dict[str, Any]) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    prefix = f"query_context[{path.name}]"

    if context.get("artifact_type") != "kb_chunk_query_context":
        failures.append(
            ValidationFailure(
                check=f"{prefix}.artifact_type",
                detail=f"Expected kb_chunk_query_context; found {context.get('artifact_type')!r}.",
            )
        )

    if context.get("schema_version") != "kb_chunk_query_context.v2":
        failures.append(
            ValidationFailure(
                check=f"{prefix}.schema_version",
                detail=f"Expected kb_chunk_query_context.v2; found {context.get('schema_version')!r}.",
            )
        )

    query = context.get("query")
    if not isinstance(query, dict):
        failures.append(ValidationFailure(check=f"{prefix}.query", detail="Expected query object."))
        return failures

    diagnostics = context.get("diagnostics")
    if not isinstance(diagnostics, dict):
        failures.append(ValidationFailure(check=f"{prefix}.diagnostics", detail="Expected diagnostics object."))
        return failures

    term_diagnostics = diagnostics.get("term_diagnostics")
    if not isinstance(term_diagnostics, dict) or not term_diagnostics:
        failures.append(
            ValidationFailure(
                check=f"{prefix}.diagnostics.term_diagnostics",
                detail="Expected non-empty term_diagnostics object.",
            )
        )
    else:
        required_term_fields = {"global_posting_count", "filtered_posting_count", "idf", "candidate_limit", "candidate_limited"}
        for term, details in term_diagnostics.items():
            if not isinstance(details, dict):
                failures.append(
                    ValidationFailure(
                        check=f"{prefix}.diagnostics.term_diagnostics.{term}",
                        detail="Expected term diagnostics entry to be an object.",
                    )
                )
                continue
            missing = sorted(required_term_fields - set(details))
            if missing:
                failures.append(
                    ValidationFailure(
                        check=f"{prefix}.diagnostics.term_diagnostics.{term}",
                        detail=f"Missing term diagnostic fields: {', '.join(missing)}.",
                    )
                )

    source_diversity = diagnostics.get("source_diversity")
    if not isinstance(source_diversity, dict):
        failures.append(
            ValidationFailure(
                check=f"{prefix}.diagnostics.source_diversity",
                detail="Expected source_diversity object.",
            )
        )
    elif "excluded_by_reason" not in source_diversity:
        failures.append(
            ValidationFailure(
                check=f"{prefix}.diagnostics.source_diversity.excluded_by_reason",
                detail="Expected source_diversity.excluded_by_reason field.",
            )
        )

    returned_count = diagnostics.get("returned_count")
    if not isinstance(returned_count, int) or returned_count <= 0:
        failures.append(
            ValidationFailure(
                check=f"{prefix}.diagnostics.returned_count",
                detail=f"Expected returned_count > 0; found {returned_count!r}.",
            )
        )

    results = context.get("results")
    if not isinstance(results, list) or not results:
        failures.append(ValidationFailure(check=f"{prefix}.results", detail="Expected non-empty results list."))
        return failures

    filters = query.get("filters") or {}
    if not isinstance(filters, dict):
        failures.append(ValidationFailure(check=f"{prefix}.query.filters", detail="Expected filters to be an object."))
        filters = {}

    for index, result in enumerate(results):
        if not isinstance(result, dict):
            failures.append(
                ValidationFailure(check=f"{prefix}.results[{index}]", detail="Expected result entry to be an object.")
            )
            continue
        contributions = result.get("term_score_contributions")
        if not isinstance(contributions, dict) or not contributions:
            failures.append(
                ValidationFailure(
                    check=f"{prefix}.results[{index}].term_score_contributions",
                    detail="Expected non-empty term_score_contributions object.",
                )
            )
        for field, expected_value in filters.items():
            if not expected_value:
                continue
            actual_value = result.get(field)
            if actual_value != expected_value:
                failures.append(
                    ValidationFailure(
                        check=f"{prefix}.results[{index}].{field}",
                        detail=f"Filter mismatch: expected {expected_value!r}; found {actual_value!r}.",
                    )
                )

    return failures


def validate(query_context_root: Path, *, min_contexts: int) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    files = query_context_files(query_context_root)
    if len(files) < min_contexts:
        return [
            ValidationFailure(
                check="query_context.count",
                detail=f"Expected at least {min_contexts} query context artifact(s); found {len(files)} under {query_context_root}.",
            )
        ]

    newest = files[:min_contexts]
    saw_filtered_context = False
    saw_diversity_enabled = False
    for path in newest:
        context = read_json(path)
        failures.extend(validate_context(path, context))
        query = context.get("query", {}) if isinstance(context.get("query"), dict) else {}
        diagnostics = context.get("diagnostics", {}) if isinstance(context.get("diagnostics"), dict) else {}
        if query.get("filters"):
            saw_filtered_context = True
        source_diversity = diagnostics.get("source_diversity", {}) if isinstance(diagnostics.get("source_diversity"), dict) else {}
        if source_diversity.get("enabled"):
            saw_diversity_enabled = True

    if not saw_filtered_context:
        failures.append(
            ValidationFailure(
                check="query_context.filtered_context",
                detail=f"Expected at least one of the newest {min_contexts} query contexts to include active filters.",
            )
        )
    if not saw_diversity_enabled:
        failures.append(
            ValidationFailure(
                check="query_context.source_diversity_enabled",
                detail=f"Expected at least one of the newest {min_contexts} query contexts to enable source diversity controls.",
            )
        )

    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 4 KB retrieval diagnostic query context artifacts.")
    parser.add_argument(
        "--query-context-root",
        type=Path,
        default=root / "kbs" / "query_context",
        help="Directory containing query context artifacts.",
    )
    parser.add_argument(
        "--min-contexts",
        type=int,
        default=2,
        help="Number of newest query contexts to validate.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate(args.query_context_root, min_contexts=args.min_contexts)

    if failures:
        print("[gate4:validate] FAILED")
        for failure in failures:
            print(f"[gate4:validate] {failure.check}: {failure.detail}")
        raise SystemExit(1)

    print("[gate4:validate] OK")
    print(f"[gate4:validate] query_context_root={args.query_context_root}")
    print(f"[gate4:validate] min_contexts={args.min_contexts}")


if __name__ == "__main__":
    main()
