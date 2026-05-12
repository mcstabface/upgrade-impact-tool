from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import relpath, repo_root


@dataclass(frozen=True)
class ImpactEvidenceItem:
    evidence_id: str
    source: str
    case_id: str
    query: str
    ranker: str
    rank: int
    score: float
    chunk_id: str
    matched_terms: list[str]
    kb_document_id: str | None
    maintenance_pack: str | None
    bug_patch_number: str | None
    product: str | None
    category: str | None
    portfolio_file: str | None
    child_pdf_path: str | None
    child_sha256: str | None
    collection_path: str | None
    source_artifact_path: str | None
    chunk_index: int
    chunk_count: int
    start_char: int
    end_char: int
    text_sha256: str | None
    text: str


@dataclass(frozen=True)
class ImpactEvidenceGroup:
    group_key: str
    kb_document_id: str | None
    bug_patch_number: str | None
    product: str | None
    category: str | None
    evidence_count: int
    max_score: float
    child_pdf_paths: list[str]
    evidence_ids: list[str]


@dataclass(frozen=True)
class KBImpactContextArtifact:
    artifact_type: str
    schema_version: str
    generated_utc: str
    assembly_status: str
    generation_policy: dict[str, Any]
    source_inputs: dict[str, Any]
    target_context: dict[str, Any]
    diagnostics: dict[str, Any]
    warnings: list[str]
    evidence_groups: list[ImpactEvidenceGroup]
    evidence_items: list[ImpactEvidenceItem]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def stable_evidence_id(case_id: str, chunk_id: str) -> str:
    return hashlib.sha256(f"{case_id}\n{chunk_id}".encode("utf-8")).hexdigest()[:16]


def connect_index(index_path: Path) -> sqlite3.Connection:
    if not index_path.exists():
        raise FileNotFoundError(f"SQLite index not found: {index_path}")
    conn = sqlite3.connect(index_path)
    conn.row_factory = sqlite3.Row
    return conn


def fetch_chunks(index_path: Path, chunk_ids: list[str]) -> dict[str, sqlite3.Row]:
    if not chunk_ids:
        return {}
    with connect_index(index_path) as conn:
        placeholders = ",".join("?" for _ in chunk_ids)
        rows = conn.execute(f"SELECT * FROM chunks WHERE chunk_id IN ({placeholders})", chunk_ids).fetchall()
    return {row["chunk_id"]: row for row in rows}


def collect_eval_chunk_refs(eval_results: dict[str, Any], *, max_results_per_case: int) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for case in eval_results.get("results", []):
        if case.get("status") != "PASS":
            continue
        for result in case.get("top_results", [])[:max_results_per_case]:
            chunk_id = result.get("chunk_id")
            if not chunk_id:
                continue
            refs.append(
                {
                    "case_id": case.get("case_id"),
                    "query": case.get("query"),
                    "ranker": case.get("ranker"),
                    "rank": result.get("rank"),
                    "score": result.get("score"),
                    "matched_terms": result.get("matched_terms") or [],
                    "chunk_id": chunk_id,
                }
            )
    return refs


def build_evidence_items(refs: list[dict[str, Any]], chunk_rows: dict[str, sqlite3.Row]) -> tuple[list[ImpactEvidenceItem], list[str]]:
    items: list[ImpactEvidenceItem] = []
    warnings: list[str] = []
    seen: set[tuple[str, str]] = set()

    for ref in refs:
        chunk_id = ref["chunk_id"]
        row = chunk_rows.get(chunk_id)
        if row is None:
            warnings.append(f"Missing chunk row for chunk_id={chunk_id}")
            continue
        key = (str(ref.get("case_id")), chunk_id)
        if key in seen:
            continue
        seen.add(key)
        text = row["text"] or ""
        items.append(
            ImpactEvidenceItem(
                evidence_id=stable_evidence_id(str(ref.get("case_id")), chunk_id),
                source="kb_retrieval_eval_results",
                case_id=str(ref.get("case_id")),
                query=str(ref.get("query")),
                ranker=str(ref.get("ranker")),
                rank=int(ref.get("rank") or 0),
                score=float(ref.get("score") or 0.0),
                chunk_id=chunk_id,
                matched_terms=list(ref.get("matched_terms") or []),
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
                chunk_index=int(row["chunk_index"] or 0),
                chunk_count=int(row["chunk_count"] or 0),
                start_char=int(row["start_char"] or 0),
                end_char=int(row["end_char"] or 0),
                text_sha256=row["text_sha256"] or sha256_text(text),
                text=text,
            )
        )
    return items, warnings


def build_groups(items: list[ImpactEvidenceItem]) -> list[ImpactEvidenceGroup]:
    grouped: dict[str, list[ImpactEvidenceItem]] = defaultdict(list)
    for item in items:
        group_key = "::".join(
            [
                item.kb_document_id or "UNKNOWN_KB",
                item.bug_patch_number or "UNKNOWN_BUG_PATCH",
                item.product or "UNKNOWN_PRODUCT",
                item.category or "UNKNOWN_CATEGORY",
            ]
        )
        grouped[group_key].append(item)

    groups: list[ImpactEvidenceGroup] = []
    for group_key, group_items in grouped.items():
        first = group_items[0]
        groups.append(
            ImpactEvidenceGroup(
                group_key=group_key,
                kb_document_id=first.kb_document_id,
                bug_patch_number=first.bug_patch_number,
                product=first.product,
                category=first.category,
                evidence_count=len(group_items),
                max_score=max(item.score for item in group_items),
                child_pdf_paths=sorted({item.child_pdf_path for item in group_items if item.child_pdf_path}),
                evidence_ids=sorted(item.evidence_id for item in group_items),
            )
        )
    return sorted(groups, key=lambda group: (-group.max_score, group.group_key))


def build_context(
    *,
    eval_results_path: Path,
    index_path: Path,
    output_path: Path,
    max_results_per_case: int,
) -> KBImpactContextArtifact:
    root = repo_root()
    eval_results = read_json(eval_results_path)
    refs = collect_eval_chunk_refs(eval_results, max_results_per_case=max_results_per_case)
    chunk_rows = fetch_chunks(index_path, sorted({ref["chunk_id"] for ref in refs}))
    items, warnings = build_evidence_items(refs, chunk_rows)
    groups = build_groups(items)

    if eval_results.get("failed_count", 0):
        warnings.append("Source evaluation results contain failed cases; impact context should be reviewed before downstream use.")
    if not items:
        warnings.append("No evidence items were assembled.")

    return KBImpactContextArtifact(
        artifact_type="kb_impact_context",
        schema_version="kb_impact_context.v1",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        assembly_status="EVIDENCE_ONLY_NO_GENERATED_CLAIMS",
        generation_policy={
            "llm_used": False,
            "impact_claims_generated": False,
            "summaries_generated": False,
            "allowed_use": "Evidence packet for reviewer inspection and later constrained impact-draft generation.",
            "prohibited_use": "Do not treat this artifact as an impact analysis or business conclusion.",
        },
        source_inputs={
            "eval_results_path": relpath(eval_results_path, root),
            "index_path": relpath(index_path, root),
            "max_results_per_case": max_results_per_case,
            "output_path": relpath(output_path, root),
        },
        target_context={
            "source_eval_case_count": eval_results.get("case_count", 0),
            "source_eval_passed_count": eval_results.get("passed_count", 0),
            "source_eval_failed_count": eval_results.get("failed_count", 0),
            "source_queries": sorted({str(result.get("query")) for result in eval_results.get("results", [])}),
            "source_rankers": sorted({str(result.get("ranker")) for result in eval_results.get("results", [])}),
        },
        diagnostics={
            "retrieval_refs": len(refs),
            "assembled_evidence_items": len(items),
            "evidence_groups": len(groups),
            "unique_bug_patch_numbers": len({item.bug_patch_number for item in items if item.bug_patch_number}),
            "unique_child_pdfs": len({item.child_pdf_path for item in items if item.child_pdf_path}),
        },
        warnings=warnings,
        evidence_groups=groups,
        evidence_items=items,
    )


def write_context(context: KBImpactContextArtifact, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(context), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Assemble Gate 6 evidence-only impact context from retrieval evaluation results.")
    parser.add_argument(
        "--eval-results",
        type=Path,
        default=root / "kbs" / "manifests" / "kb_retrieval_eval_results.json",
        help="Path to retrieval evaluation results JSON.",
    )
    parser.add_argument(
        "--index-path",
        type=Path,
        default=root / "kbs" / "indexes" / "kb_chunk_lexical_index.sqlite",
        help="Path to SQLite lexical index.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=root / "kbs" / "impact_context" / "kb_impact_context.v1.json",
        help="Impact context output path.",
    )
    parser.add_argument("--max-results-per-case", type=int, default=5, help="Maximum top retrieval results to include per eval case.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    context = build_context(
        eval_results_path=args.eval_results,
        index_path=args.index_path,
        output_path=args.output,
        max_results_per_case=args.max_results_per_case,
    )
    write_context(context, args.output)

    print(f"Wrote KB impact context: {args.output}")
    print(f"Assembly status: {context.assembly_status}")
    print(f"Evidence items: {context.diagnostics['assembled_evidence_items']}")
    print(f"Evidence groups: {context.diagnostics['evidence_groups']}")
    print(f"Warnings: {len(context.warnings)}")


if __name__ == "__main__":
    main()
