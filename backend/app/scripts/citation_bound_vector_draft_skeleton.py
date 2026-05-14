from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_DRAFT_INPUT_REPORT = "kbs/retrieval/kb_fixture_vector_draft_input.v1.json"
DEFAULT_DRAFT_SKELETON_REPORT = "kbs/retrieval/kb_fixture_vector_draft_skeleton.v1.json"


@dataclass(frozen=True)
class VectorDraftSkeletonSection:
    section_id: str
    title: str
    instruction: str
    required_evidence_ids: list[str]
    citation_labels: list[str]
    generated_text: str = ""


@dataclass(frozen=True)
class VectorDraftSkeletonReport:
    report_version: str
    status: str
    source_draft_input_report: str
    evidence_slot_count: int
    section_count: int
    sections: list[VectorDraftSkeletonSection] = field(default_factory=list)
    production_retrieval_enabled: bool = False
    draft_generation_enabled: bool = False
    llm_call_performed: bool = False


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def build_citation_bound_vector_draft_skeleton(*, draft_input_path: Path) -> VectorDraftSkeletonReport:
    if not draft_input_path.exists():
        raise FileNotFoundError(f"Draft input report not found: {draft_input_path}")
    draft_input = read_json(draft_input_path)
    if draft_input.get("status") != "VECTOR_DRAFT_INPUT_READY":
        raise ValueError(f"Draft input status must be VECTOR_DRAFT_INPUT_READY: {draft_input.get('status')}")
    if draft_input.get("production_retrieval_enabled") is not False:
        raise ValueError("Draft input must keep production_retrieval_enabled false")
    if draft_input.get("draft_generation_enabled") is not False:
        raise ValueError("Draft input must keep draft_generation_enabled false")
    evidence_slots = draft_input.get("evidence_slots")
    if not isinstance(evidence_slots, list) or not evidence_slots:
        raise ValueError("Draft input evidence_slots must be a non-empty list")
    evidence_ids: list[str] = []
    citation_labels: list[str] = []
    for slot in sorted(evidence_slots, key=lambda row: int(row.get("rank") or 0)):
        if not isinstance(slot, dict):
            raise ValueError("Evidence slot must be an object")
        evidence_id = str(slot.get("evidence_id") or "")
        citation_label = str(slot.get("citation_label") or "")
        if not evidence_id or not citation_label:
            raise ValueError("Evidence slot missing evidence_id or citation_label")
        evidence_ids.append(evidence_id)
        citation_labels.append(citation_label)
    sections = [
        VectorDraftSkeletonSection(
            section_id="vector-context-summary",
            title="Vector Context Summary",
            instruction="Summarize only the citation-bound vector evidence slots. Do not add uncited claims.",
            required_evidence_ids=evidence_ids,
            citation_labels=citation_labels,
        ),
        VectorDraftSkeletonSection(
            section_id="potential-upgrade-impact",
            title="Potential Upgrade Impact",
            instruction="Draft impact statements only from required evidence IDs when generation is explicitly enabled in a later gate.",
            required_evidence_ids=evidence_ids,
            citation_labels=citation_labels,
        ),
        VectorDraftSkeletonSection(
            section_id="review-notes",
            title="Reviewer Notes",
            instruction="Reserve space for human review notes; no automated prose is generated in this gate.",
            required_evidence_ids=[],
            citation_labels=[],
        ),
    ]
    root = repo_root()
    return VectorDraftSkeletonReport(
        report_version="1",
        status="VECTOR_DRAFT_SKELETON_READY",
        source_draft_input_report=str(draft_input_path.relative_to(root)) if draft_input_path.is_relative_to(root) else str(draft_input_path),
        evidence_slot_count=len(evidence_ids),
        section_count=len(sections),
        sections=sections,
        production_retrieval_enabled=False,
        draft_generation_enabled=False,
        llm_call_performed=False,
    )


def write_citation_bound_vector_draft_skeleton(path: Path, report: VectorDraftSkeletonReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build citation-bound vector draft skeleton.")
    parser.add_argument("--draft-input", type=Path, default=root / DEFAULT_DRAFT_INPUT_REPORT)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_DRAFT_SKELETON_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_citation_bound_vector_draft_skeleton(draft_input_path=args.draft_input)
    write_citation_bound_vector_draft_skeleton(args.output, report)
    print(f"[gate18x:draft-skeleton] Wrote vector draft skeleton: {args.output}")
    print(f"[gate18x:draft-skeleton] status={report.status}")
    print(f"[gate18x:draft-skeleton] evidence_slot_count={report.evidence_slot_count}")
    print(f"[gate18x:draft-skeleton] section_count={report.section_count}")
    print("[gate18x:draft-skeleton] draft_generation_enabled=false")
    print("[gate18x:draft-skeleton] llm_call_performed=false")


if __name__ == "__main__":
    main()
