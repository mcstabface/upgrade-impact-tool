from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_DRAFT_SKELETON_REPORT = "kbs/retrieval/kb_fixture_vector_draft_skeleton.v1.json"
DEFAULT_GENERATION_CONTRACT_REPORT = "kbs/retrieval/kb_fixture_vector_draft_generation_contract.v1.json"


@dataclass(frozen=True)
class DraftGenerationContractCheck:
    name: str
    passed: bool
    detail: str


@dataclass(frozen=True)
class DraftGenerationContractReport:
    report_version: str
    status: str
    source_draft_skeleton_report: str
    checks: list[DraftGenerationContractCheck]
    passed_count: int
    failed_count: int
    allowed_input_status: str = "VECTOR_DRAFT_SKELETON_READY"
    required_generation_flag: bool = False
    allowed_output_status: str = "GENERATION_DISABLED_CONTRACT_READY"
    generation_adapter: str = "disabled"
    production_retrieval_enabled: bool = False
    draft_generation_enabled: bool = False
    llm_call_allowed: bool = False
    llm_call_performed: bool = False
    blockers: list[str] = field(default_factory=list)


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def build_generation_contract(*, draft_skeleton_path: Path) -> DraftGenerationContractReport:
    if not draft_skeleton_path.exists():
        raise FileNotFoundError(f"Draft skeleton report not found: {draft_skeleton_path}")
    skeleton = read_json(draft_skeleton_path)
    checks: list[DraftGenerationContractCheck] = []
    blockers: list[str] = []

    def add_check(name: str, passed: bool, detail: str) -> None:
        checks.append(DraftGenerationContractCheck(name=name, passed=passed, detail=detail))
        if not passed:
            blockers.append(name)

    add_check("skeleton_status_ready", skeleton.get("status") == "VECTOR_DRAFT_SKELETON_READY", f"status={skeleton.get('status')}")
    add_check("production_retrieval_disabled", skeleton.get("production_retrieval_enabled") is False, f"production_retrieval_enabled={skeleton.get('production_retrieval_enabled')}")
    add_check("draft_generation_disabled", skeleton.get("draft_generation_enabled") is False, f"draft_generation_enabled={skeleton.get('draft_generation_enabled')}")
    add_check("llm_call_not_performed", skeleton.get("llm_call_performed") is False, f"llm_call_performed={skeleton.get('llm_call_performed')}")
    sections = skeleton.get("sections")
    add_check("sections_present", isinstance(sections, list) and len(sections) > 0, f"section_count={len(sections) if isinstance(sections, list) else 'missing'}")
    if isinstance(sections, list):
        evidence_bound_sections = [section for section in sections if isinstance(section, dict) and section.get("section_id") != "review-notes"]
        generated_text_empty = all(str(section.get("generated_text") or "") == "" for section in evidence_bound_sections)
        evidence_bindings_present = all(section.get("required_evidence_ids") and section.get("citation_labels") for section in evidence_bound_sections)
    else:
        generated_text_empty = False
        evidence_bindings_present = False
    add_check("generated_text_empty", generated_text_empty, "Evidence-bound sections must not contain generated text")
    add_check("evidence_bindings_present", evidence_bindings_present, "Evidence-bound sections require evidence IDs and citation labels")

    failed_count = sum(1 for check in checks if not check.passed)
    passed_count = len(checks) - failed_count
    root = repo_root()
    return DraftGenerationContractReport(
        report_version="1",
        status="GENERATION_DISABLED_CONTRACT_READY" if failed_count == 0 else "GENERATION_CONTRACT_BLOCKED",
        source_draft_skeleton_report=str(draft_skeleton_path.relative_to(root)) if draft_skeleton_path.is_relative_to(root) else str(draft_skeleton_path),
        checks=checks,
        passed_count=passed_count,
        failed_count=failed_count,
        allowed_input_status="VECTOR_DRAFT_SKELETON_READY",
        required_generation_flag=False,
        allowed_output_status="GENERATION_DISABLED_CONTRACT_READY",
        generation_adapter="disabled",
        production_retrieval_enabled=False,
        draft_generation_enabled=False,
        llm_call_allowed=False,
        llm_call_performed=False,
        blockers=blockers,
    )


def write_generation_contract(path: Path, report: DraftGenerationContractReport) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(report), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build citation-bound vector draft generation contract.")
    parser.add_argument("--draft-skeleton", type=Path, default=root / DEFAULT_DRAFT_SKELETON_REPORT)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_GENERATION_CONTRACT_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    report = build_generation_contract(draft_skeleton_path=args.draft_skeleton)
    write_generation_contract(args.output, report)
    print(f"[gate18y:generation-contract] Wrote draft generation contract: {args.output}")
    print(f"[gate18y:generation-contract] status={report.status}")
    print(f"[gate18y:generation-contract] passed_checks={report.passed_count}")
    print(f"[gate18y:generation-contract] failed_checks={report.failed_count}")
    print("[gate18y:generation-contract] draft_generation_enabled=false")
    print("[gate18y:generation-contract] llm_call_allowed=false")


if __name__ == "__main__":
    main()
