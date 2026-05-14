from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_CITATION_JOIN_REPORT = "kbs/retrieval/kb_fixture_vector_citation_join.v1.json"
DEFAULT_VECTOR_CONTEXT_REPORT = "kbs/retrieval/kb_fixture_vector_context.v1.json"


@dataclass(frozen=True)
class CitationBoundVectorContextItem:
    rank: int
    score: float
    chunk_id: str
    vector_record_id: str
    request_id: str
    source_artifact_path: str
    kb_document_id: str
    bug_patch_number: str
    child_sha256: str
    citation_label: str


@dataclass(frozen=True)
class CitationBoundVectorContextReport:
    report_version: str
    status: str
    source_citation_join_report: str
    context_item_count: int
    context_items: list[CitationBoundVectorContextItem] = field(default_factory=list)
    production_retrieval_enabled: bool = False
    impact_generation_enabled: bool = False


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def citation_label_for(item: dict[str, Any]) -> str:
    kb_document_id = str(item.get("kb_document_id") or "")
    bug_patch_number = str(item.get("bug_patch_number") or "")
    rank = int(item.get("rank") or 0)
    return f"vector-rank-{rank}:{kb_document_id}:{bug_patch_number}"


def build_citation_bound_vector_context(*, citation_join_report_path: Path) -> CitationBoundVectorContextReport:
    if not citation_join_report_path.exists():
        raise FileNotFoundError(f"Citation join report not found: {citation_join_report_path}")
    join_report = read_json(citation_join_report_path)
    if join_report.get("status") != "CITATION_JOIN_OK":
        raise ValueError(f"Citation join report status must be CITATION_JOIN_OK: {join_report.get('status')}")
    if join_report.get("production_retrieval_enabled") is not False:
        raise ValueError("Citation join report must keep production_retrieval_enabled false")
    results = join_report.get("results")
    if not isinstance(results, list):
        raise ValueError("Citation join results must be a list")

    context_items: list[CitationBoundVectorContextItem] = []
    for item in results:
        if not isinstance(item, dict):
            raise ValueError("Citation join result must be an object")
        required_fields = [
            "rank",
            "score",
            "chunk_id",
            "vector_record_id",
            "request_id",
            "source_artifact_path",
            "kb_document_id",
            "bug_patch_number",
            "child_sha256",
        ]
        missing = [field_name for field_name in required_fields if str(item.get(field_name) or "") == ""]
        if missing:
            raise ValueError(f"Citation join result missing required fields: {missing}")
        context_items.append(
            CitationBoundVectorContextItem(
                rank=int(item["rank"]),
                score=float(item["score"]),
                chunk_id=str(item["chunk_id"]),
                vector_record_id=str(item["vector_record_id"]),
                request_id=str(item["request_id"]),
                source_artifact_path=str(item["source_artifact_path"]),
                kb_document_id=str(item["kb_document_id"]),
                bug_patch_number=str(item["bug_patch_number"]),
                child_sha256=str(item["child_sha256"]),
                citation_label=citation_label_for(item),
            )
        )
    context_items.sort(key=lambda row: row.rank)
    root = repo_root()
    return CitationBoundVectorContextReport(
        report_version="1",
        status="CITATION_BOUND_VECTOR_CONTEXT_READY",
        source_citation_join_report=str(citation_join_report_path.relative_to(root)) if citation_join_report_path.is_relative_to(root) else str(citation_join_report_path),
        context_item_count=len(context_items),
        context_items=context_items,
        production_retrieval_enabled=False,
        impact_generation_enabled=False,
    )


def write_citation_bound_vector_context(path: Path, report: CitationBoundVectorContextReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Assemble citation-bound fixture vector context.")
    parser.add_argument("--citation-join-report", type=Path, default=root / DEFAULT_CITATION_JOIN_REPORT)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_VECTOR_CONTEXT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_citation_bound_vector_context(citation_join_report_path=args.citation_join_report)
    write_citation_bound_vector_context(args.output, report)
    print(f"[gate18v:context] Wrote citation-bound vector context: {args.output}")
    print(f"[gate18v:context] status={report.status}")
    print(f"[gate18v:context] context_item_count={report.context_item_count}")
    print("[gate18v:context] production_retrieval_enabled=false")
    print("[gate18v:context] impact_generation_enabled=false")


if __name__ == "__main__":
    main()
