from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


@dataclass(frozen=True)
class ValidationFailure:
    check: str
    detail: str


def read_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def validate_enriched_context(context: dict) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    if context.get("artifact_type") != "kb_impact_context":
        failures.append(ValidationFailure("context.artifact_type", "Expected kb_impact_context."))
    if context.get("schema_version") != "kb_impact_context.v2":
        failures.append(ValidationFailure("context.schema_version", f"Expected kb_impact_context.v2; found {context.get('schema_version')!r}."))
    if context.get("assembly_status") != "ENRICHED_EVIDENCE_ONLY_NO_GENERATED_CLAIMS":
        failures.append(ValidationFailure("context.assembly_status", "Expected enriched evidence-only no-claims status."))

    policy = context.get("generation_policy") or {}
    for field in ["llm_used", "impact_claims_generated", "summaries_generated"]:
        if policy.get(field) is not False:
            failures.append(ValidationFailure(f"context.generation_policy.{field}", f"Expected False; found {policy.get(field)!r}."))

    items = context.get("evidence_items") or []
    if not items:
        failures.append(ValidationFailure("context.evidence_items", "Expected non-empty evidence items."))
    for index, item in enumerate(items):
        flags = item.get("pdf_context_flags")
        if not isinstance(flags, dict):
            failures.append(ValidationFailure(f"context.evidence_items[{index}].pdf_context_flags", "Expected PDF context flags."))
        elif flags.get("status") != "FOUND":
            failures.append(ValidationFailure(f"context.evidence_items[{index}].pdf_context_flags.status", f"Expected FOUND; got {flags.get('status')!r}."))

    exception_context = context.get("evidence_exception_context")
    if not isinstance(exception_context, dict):
        failures.append(ValidationFailure("context.evidence_exception_context", "Expected evidence exception context."))
    elif "high_severity_exceptions" not in exception_context:
        failures.append(ValidationFailure("context.evidence_exception_context.high_severity_exceptions", "Expected high severity exceptions list."))

    return failures


def validate_skeleton(skeleton: dict, context: dict) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    if skeleton.get("artifact_type") != "kb_impact_draft_skeleton":
        failures.append(ValidationFailure("skeleton.artifact_type", "Expected kb_impact_draft_skeleton."))
    if skeleton.get("schema_version") != "kb_impact_draft_skeleton.v1":
        failures.append(ValidationFailure("skeleton.schema_version", "Expected kb_impact_draft_skeleton.v1."))
    if skeleton.get("skeleton_status") != "STRUCTURE_ONLY_NO_GENERATED_CLAIMS":
        failures.append(ValidationFailure("skeleton.skeleton_status", "Expected structure-only no-claims status."))

    policy = skeleton.get("generation_policy") or {}
    for field in ["llm_used", "impact_claims_generated", "narrative_generated"]:
        if policy.get(field) is not False:
            failures.append(ValidationFailure(f"skeleton.generation_policy.{field}", f"Expected False; found {policy.get(field)!r}."))

    context_evidence_ids = {item.get("evidence_id") for item in context.get("evidence_items", []) if item.get("evidence_id")}
    sections = skeleton.get("sections") or []
    if not sections:
        failures.append(ValidationFailure("skeleton.sections", "Expected non-empty sections."))
    required_sections = {"scope_and_inputs", "evidence_groups", "assumptions", "unresolved_evidence_gaps", "reviewer_notes", "no_generated_conclusion_status"}
    actual_sections = {section.get("section_id") for section in sections if isinstance(section, dict)}
    missing_sections = sorted(required_sections - actual_sections)
    if missing_sections:
        failures.append(ValidationFailure("skeleton.sections.required", f"Missing required sections: {', '.join(missing_sections)}."))

    forbidden_fragments = ["therefore", "impact is", "will impact", "business impact", "root cause is"]
    for index, section in enumerate(sections):
        if not isinstance(section, dict):
            failures.append(ValidationFailure(f"skeleton.sections[{index}]", "Expected section object."))
            continue
        status = section.get("status") or ""
        if "NO_GENERATED" not in status and status != "STRUCTURE_ONLY_NO_GENERATED_CLAIMS":
            failures.append(ValidationFailure(f"skeleton.sections[{index}].status", f"Unexpected status: {status!r}."))
        for evidence_id in section.get("evidence_ids") or []:
            if evidence_id not in context_evidence_ids:
                failures.append(ValidationFailure(f"skeleton.sections[{index}].evidence_ids", f"Unknown evidence ID: {evidence_id}."))
        content = str(section.get("content") or "").lower()
        for fragment in forbidden_fragments:
            if fragment in content:
                failures.append(ValidationFailure(f"skeleton.sections[{index}].content", f"Forbidden generated-claim fragment found: {fragment!r}."))

    return failures


def validate(context_path: Path, skeleton_path: Path) -> list[ValidationFailure]:
    context = read_json(context_path)
    skeleton = read_json(skeleton_path)
    failures = validate_enriched_context(context)
    failures.extend(validate_skeleton(skeleton, context))
    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 7 enriched context and draft skeleton artifacts.")
    parser.add_argument("--context", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_context.v2.enriched.json")
    parser.add_argument("--skeleton", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_draft_skeleton.v1.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate(args.context, args.skeleton)
    if failures:
        print("[gate7:validate] FAILED")
        for failure in failures:
            print(f"[gate7:validate] {failure.check}: {failure.detail}")
        raise SystemExit(1)
    print("[gate7:validate] OK")
    print(f"[gate7:validate] context={args.context}")
    print(f"[gate7:validate] skeleton={args.skeleton}")


if __name__ == "__main__":
    main()
