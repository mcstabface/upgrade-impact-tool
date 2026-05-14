from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_VECTOR_CONTEXT_REPORT = "kbs/retrieval/kb_fixture_vector_context.v1.json"
DEFAULT_DRAFT_INPUT_REPORT = "kbs/retrieval/kb_fixture_vector_draft_input.v1.json"


@dataclass(frozen=True)
class VectorDraftEvidenceSlot:
    evidence_id: str
    rank: int
    score: float
    chunk_id: str
    citation_label: str
    source_artifact_path: str
    kb_document_id: str
    bug_patch_number: str
    child_sha256: str


@dataclass(frozen=True)
class VectorDraftInputReport:
    report_version: str
    status: str
    source_vector_context_report: str
    evidence_slot_count: int
    evidence_slots: list[VectorDraftEvidenceSlot] = field(default_factory=list)
    adapter_mode: str = "fixture_vector_context_to_draft_input"
    production_retrieval_enabled: bool = False
    draft_generation_enabled: bool = False


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def build_vector_draft_input(*, vector_context_path: Path) -> VectorDraftInputReport:
    if not vector_context_path.exists():
        raise FileNotFoundError(f"Vector context report not found: {vector_context_path}")
    context = read_json(vector_context_path)
    if context.get("status") != "CITATION_BOUND_VECTOR_CONTEXT_READY":
        raise ValueError(f"Vector context status must be CITATION_BOUND_VECTOR_CONTEXT_READY: {context.get('status')}")
    if context.get("production_retrieval_enabled") is not False:
        raise ValueError("Vector context must keep production_retrieval_enabled false")
    if context.get("impact_generation_enabled") is not False:
        raise ValueError("Vector context must keep impact_generation_enabled false")
    items = context.get("context_items")
    if not isinstance(items, list):
        raise ValueError("Vector context items must be a list")

    evidence_slots: list[VectorDraftEvidenceSlot] = []
    for item in sorted(items, key=lambda row: int(row.get("rank") or 0)):
        if not isinstance(item, dict):
            raise ValueError("Vector context item must be an object")
        rank = int(item.get("rank") or 0)
        required_fields = [
            "score",
            "chunk_id",
            "citation_label",
            "source_artifact_path",
            "kb_document_id",
            "bug_patch_number",
            "child_sha256",
        ]
        missing = [field_name for field_name in required_fields if str(item.get(field_name) or "") == ""]
        if rank <= 0 or missing:
            raise ValueError(f"Vector context item is not draft-input ready: rank={rank} missing={missing}")
        evidence_slots.append(
            VectorDraftEvidenceSlot(
                evidence_id=f"vector-evidence-{rank:04d}",
                rank=rank,
                score=float(item["score"]),
                chunk_id=str(item["chunk_id"]),
                citation_label=str(item["citation_label"]),
                source_artifact_path=str(item["source_artifact_path"]),
                kb_document_id=str(item["kb_document_id"]),
                bug_patch_number=str(item["bug_patch_number"]),
                child_sha256=str(item["child_sha256"]),
            )
        )
    root = repo_root()
    return VectorDraftInputReport(
        report_version="1",
        status="VECTOR_DRAFT_INPUT_READY",
        source_vector_context_report=str(vector_context_path.relative_to(root)) if vector_context_path.is_relative_to(root) else str(vector_context_path),
        evidence_slot_count=len(evidence_slots),
        evidence_slots=evidence_slots,
        adapter_mode="fixture_vector_context_to_draft_input",
        production_retrieval_enabled=False,
        draft_generation_enabled=False,
    )


def write_vector_draft_input(path: Path, report: VectorDraftInputReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Adapt fixture vector context to draft input contract.")
    parser.add_argument("--vector-context", type=Path, default=root / DEFAULT_VECTOR_CONTEXT_REPORT)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_DRAFT_INPUT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_vector_draft_input(vector_context_path=args.vector_context)
    write_vector_draft_input(args.output, report)
    print(f"[gate18w:draft-input] Wrote vector draft input: {args.output}")
    print(f"[gate18w:draft-input] status={report.status}")
    print(f"[gate18w:draft-input] evidence_slot_count={report.evidence_slot_count}")
    print("[gate18w:draft-input] production_retrieval_enabled=false")
    print("[gate18w:draft-input] draft_generation_enabled=false")


if __name__ == "__main__":
    main()
