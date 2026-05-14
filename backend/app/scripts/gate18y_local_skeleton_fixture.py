from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def local_skeleton_fixture() -> dict[str, Any]:
    evidence_ids = ["vector-evidence-0001", "vector-evidence-0002", "vector-evidence-0003"]
    citation_labels = [
        "vector-rank-1:KB881136:39007114",
        "vector-rank-2:KB881136:38966530",
        "vector-rank-3:KB881135:39127058",
    ]
    return {
        "report_version": "1",
        "status": "VECTOR_DRAFT_SKELETON_READY",
        "source_draft_input_report": "local_gate18y_fixture",
        "evidence_slot_count": len(evidence_ids),
        "section_count": 3,
        "production_retrieval_enabled": False,
        "draft_generation_enabled": False,
        "llm_call_performed": False,
        "sections": [
            {
                "section_id": "vector-context-summary",
                "title": "Vector Context Summary",
                "instruction": "Use only required evidence IDs and citation labels.",
                "required_evidence_ids": evidence_ids,
                "citation_labels": citation_labels,
                "generated_text": "",
            },
            {
                "section_id": "potential-upgrade-impact",
                "title": "Potential Upgrade Impact",
                "instruction": "Do not write prose unless a later gate enables generation.",
                "required_evidence_ids": evidence_ids,
                "citation_labels": citation_labels,
                "generated_text": "",
            },
            {
                "section_id": "review-notes",
                "title": "Reviewer Notes",
                "instruction": "Human review placeholder.",
                "required_evidence_ids": [],
                "citation_labels": [],
                "generated_text": "",
            },
        ],
    }


def ensure_local_skeleton_fixture(path: Path) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(local_skeleton_fixture(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
