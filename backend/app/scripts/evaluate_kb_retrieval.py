from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.query_kb_chunks import clean_filters, query_index


@dataclass(frozen=True)
class CaseResult:
    case_id: str
    status: str
    query: str
    ranker: str
    returned_count: int
    failures: list[str] = field(default_factory=list)
    top_results: list[dict[str, Any]] = field(default_factory=list)


@dataclass(frozen=True)
class EvaluationResult:
    artifact_type: str
    schema_version: str
    generated_utc: str
    eval_set_path: str
    index_path: str
    case_count: int
    passed_count: int
    failed_count: int
    results: list[CaseResult]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def result_summary(result: Any) -> dict[str, Any]:
    return {
        "rank": result.rank,
        "score": result.score,
        "chunk_id": result.chunk_id,
        "kb_document_id": result.kb_document_id,
        "bug_patch_number": result.bug_patch_number,
        "product": result.product,
        "category": result.category,
        "matched_terms": result.matched_terms,
    }


def check_expect_all(results: list[Any], expectations: dict[str, Any]) -> list[str]:
    failures: list[str] = []
    for field, expected_value in expectations.items():
        mismatches = [result for result in results if getattr(result, field, None) != expected_value]
        if mismatches:
            failures.append(
                f"expect_all failed for {field}: expected {expected_value!r}; "
                f"{len(mismatches)} of {len(results)} result(s) differed."
            )
    return failures


def check_expect_any(results: list[Any], expectations: dict[str, list[Any]]) -> list[str]:
    failures: list[str] = []
    for field, expected_values in expectations.items():
        expected_set = set(expected_values)
        if not any(getattr(result, field, None) in expected_set for result in results):
            failures.append(
                f"expect_any failed for {field}: expected one of {sorted(expected_set)!r}; "
                "no returned result matched."
            )
    return failures


def evaluate_case(case: dict[str, Any], *, index_path: Path) -> CaseResult:
    query = case["query"]
    ranker = case.get("ranker", "bm25")
    filters = clean_filters(case.get("filters") or {})
    context = query_index(
        index_path,
        query,
        top_k=int(case.get("top_k", 5)),
        limit_candidates=int(case.get("limit_candidates", 5000)),
        filters=filters,
        max_chunks_per_child_pdf=case.get("max_chunks_per_child_pdf"),
        max_chunks_per_bug_patch=case.get("max_chunks_per_bug_patch"),
        ranker=ranker,
        bm25_k1=float(case.get("bm25_k1", 1.2)),
        bm25_b=float(case.get("bm25_b", 0.75)),
    )

    failures: list[str] = []
    if not context.results:
        failures.append("query returned no results")

    failures.extend(check_expect_all(context.results, case.get("expect_all") or {}))
    failures.extend(check_expect_any(context.results, case.get("expect_any") or {}))

    return CaseResult(
        case_id=case["case_id"],
        status="PASS" if not failures else "FAIL",
        query=query,
        ranker=str(context.diagnostics.get("ranker")),
        returned_count=len(context.results),
        failures=failures,
        top_results=[result_summary(result) for result in context.results[:5]],
    )


def evaluate(eval_set_path: Path, index_path: Path) -> EvaluationResult:
    root = repo_root()
    eval_set = read_json(eval_set_path)
    cases = eval_set.get("cases", [])
    results = [evaluate_case(case, index_path=index_path) for case in cases]
    passed_count = sum(1 for result in results if result.status == "PASS")
    failed_count = len(results) - passed_count

    return EvaluationResult(
        artifact_type="kb_retrieval_evaluation",
        schema_version="kb_retrieval_evaluation.v1",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        eval_set_path=str(eval_set_path.relative_to(root)) if eval_set_path.is_relative_to(root) else str(eval_set_path),
        index_path=str(index_path.relative_to(root)) if index_path.is_relative_to(root) else str(index_path),
        case_count=len(results),
        passed_count=passed_count,
        failed_count=failed_count,
        results=results,
    )


def write_json_artifact(artifact: EvaluationResult, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(artifact), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_markdown_summary(artifact: EvaluationResult, output_path: Path) -> None:
    lines: list[str] = []
    lines.append("# KB Retrieval Evaluation Summary")
    lines.append("")
    lines.append(f"Generated UTC: `{artifact.generated_utc}`")
    lines.append("")
    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Evaluation set: `{artifact.eval_set_path}`")
    lines.append(f"- Index path: `{artifact.index_path}`")
    lines.append(f"- Cases: {artifact.case_count}")
    lines.append(f"- Passed: {artifact.passed_count}")
    lines.append(f"- Failed: {artifact.failed_count}")
    lines.append("")
    lines.append("## Case Results")
    lines.append("")
    lines.append("| Case | Status | Query | Ranker | Returned | Failures |")
    lines.append("|---|---|---|---|---:|---|")
    for result in artifact.results:
        failures = "; ".join(result.failures) if result.failures else ""
        lines.append(
            "| "
            f"{result.case_id} | "
            f"{result.status} | "
            f"{result.query} | "
            f"{result.ranker} | "
            f"{result.returned_count} | "
            f"{failures} |"
        )
    lines.append("")
    lines.append("## Top Results by Case")
    lines.append("")
    for result in artifact.results:
        lines.append(f"### {result.case_id}")
        lines.append("")
        lines.append("| Rank | Score | KB | Bug / Patch | Product | Category | Matched Terms |")
        lines.append("|---:|---:|---|---|---|---|---|")
        for item in result.top_results:
            lines.append(
                "| "
                f"{item.get('rank')} | "
                f"{item.get('score')} | "
                f"{item.get('kb_document_id')} | "
                f"{item.get('bug_patch_number')} | "
                f"{item.get('product')} | "
                f"{item.get('category')} | "
                f"{', '.join(item.get('matched_terms') or [])} |"
            )
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run deterministic retrieval evaluation cases against the KB chunk index.")
    parser.add_argument(
        "--eval-set",
        type=Path,
        default=root / "kbs" / "eval" / "kb_retrieval_eval_set.json",
        help="Evaluation fixture path.",
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=root / "kbs" / "indexes" / "kb_chunk_lexical_index.sqlite",
        help="SQLite lexical index path.",
    )
    parser.add_argument(
        "--json-output",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_retrieval_eval_results.json",
        help="Evaluation JSON artifact output path.",
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_retrieval_eval_summary.md",
        help="Evaluation Markdown summary output path.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    artifact = evaluate(args.eval_set, args.index_path)
    write_json_artifact(artifact, args.json_output)
    write_markdown_summary(artifact, args.summary_output)

    print(f"Wrote KB retrieval evaluation results: {args.json_output}")
    print(f"Wrote KB retrieval evaluation summary: {args.summary_output}")
    print(f"Cases: {artifact.case_count}")
    print(f"Passed: {artifact.passed_count}")
    print(f"Failed: {artifact.failed_count}")

    if artifact.failed_count:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
