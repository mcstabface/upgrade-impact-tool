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


def validate_policy(draft: dict) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    if draft.get("artifact_type") != "kb_impact_draft":
        failures.append(ValidationFailure("artifact_type", f"Expected kb_impact_draft; found {draft.get('artifact_type')!r}."))
    if draft.get("schema_version") != "kb_impact_draft.v1":
        failures.append(ValidationFailure("schema_version", f"Expected kb_impact_draft.v1; found {draft.get('schema_version')!r}."))
    if draft.get("draft_status") != "DRAFT_CITATION_BOUND_NOT_REVIEWED_NOT_FINAL":
        failures.append(ValidationFailure("draft_status", f"Unexpected draft status: {draft.get('draft_status')!r}."))

    policy = draft.get("generation_policy") or {}
    expected = {
        "llm_used": False,
        "external_claims_allowed": False,
        "claims_require_evidence_ids": True,
        "missing_evidence_can_create_impact_claims": False,
        "image_bearing_evidence_requires_visual_review_caveat": True,
    }
    for field, expected_value in expected.items():
        if policy.get(field) is not expected_value:
            failures.append(ValidationFailure(f"generation_policy.{field}", f"Expected {expected_value!r}; found {policy.get(field)!r}."))
    if policy.get("draft_review_status") != "NOT_REVIEWED_NOT_FINAL":
        failures.append(ValidationFailure("generation_policy.draft_review_status", "Expected NOT_REVIEWED_NOT_FINAL."))
    return failures


def validate_claims(draft: dict, context: dict) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    evidence_ids = {item.get("evidence_id") for item in context.get("evidence_items", []) if item.get("evidence_id")}
    image_bearing_ids = {
        item.get("evidence_id")
        for item in context.get("evidence_items", [])
        if item.get("evidence_id") and (item.get("pdf_context_flags") or {}).get("has_images")
    }
    sections = draft.get("sections") or []
    if not sections:
        return [ValidationFailure("sections", "Expected non-empty sections.")]

    claim_count = 0
    cited_claim_count = 0
    for section_index, section in enumerate(sections):
        if not isinstance(section, dict):
            failures.append(ValidationFailure(f"sections[{section_index}]", "Expected section object."))
            continue
        if section.get("status") in {"FINAL", "REVIEWED", "APPROVED"}:
            failures.append(ValidationFailure(f"sections[{section_index}].status", "Draft section cannot be final/reviewed/approved."))
        for claim_index, claim in enumerate(section.get("claims") or []):
            claim_count += 1
            evidence_refs = claim.get("evidence_ids") or []
            claim_type = claim.get("claim_type")
            text = str(claim.get("text") or "")
            if claim_type not in {"missing_evidence_inventory", "draft_status"}:
                if not evidence_refs:
                    failures.append(
                        ValidationFailure(
                            f"sections[{section_index}].claims[{claim_index}].evidence_ids",
                            "Evidence-backed claim is missing evidence IDs.",
                        )
                    )
                else:
                    cited_claim_count += 1
            for evidence_id in evidence_refs:
                if evidence_id not in evidence_ids:
                    failures.append(
                        ValidationFailure(
                            f"sections[{section_index}].claims[{claim_index}].evidence_ids",
                            f"Unknown evidence ID: {evidence_id}.",
                        )
                    )
            if evidence_refs and "[evidence:" not in text:
                failures.append(
                    ValidationFailure(
                        f"sections[{section_index}].claims[{claim_index}].text",
                        "Claim with evidence IDs must include an inline [evidence: ...] citation marker.",
                    )
                )
            if set(evidence_refs) & image_bearing_ids:
                caveats = " ".join(claim.get("caveats") or []).lower()
                if "visual inspection" not in caveats and "visual review" not in caveats:
                    failures.append(
                        ValidationFailure(
                            f"sections[{section_index}].claims[{claim_index}].caveats",
                            "Claim citing image-bearing evidence must include visual inspection/review caveat.",
                        )
                    )
            lowered = text.lower()
            forbidden = ["final impact", "approved impact", "business conclusion", "root cause is proven"]
            for fragment in forbidden:
                if fragment in lowered:
                    failures.append(
                        ValidationFailure(
                            f"sections[{section_index}].claims[{claim_index}].text",
                            f"Forbidden final/conclusive fragment found: {fragment!r}.",
                        )
                    )
    if claim_count <= 0:
        failures.append(ValidationFailure("claims", "Expected at least one draft claim."))
    if cited_claim_count <= 0:
        failures.append(ValidationFailure("claims.cited", "Expected at least one cited evidence-backed claim."))
    return failures


def validate_gaps(draft: dict, context: dict) -> list[ValidationFailure]:
    failures: list[ValidationFailure] = []
    high_severity = (context.get("evidence_exception_context") or {}).get("high_severity_exceptions") or []
    expected_gap_count = len(high_severity)
    actual_gaps = []
    for section in draft.get("sections") or []:
        actual_gaps.extend(section.get("unresolved_gaps") or [])
    if expected_gap_count and len(actual_gaps) != expected_gap_count:
        failures.append(
            ValidationFailure(
                "unresolved_gaps.count",
                f"Expected {expected_gap_count} unresolved gaps from high-severity exceptions; found {len(actual_gaps)}.",
            )
        )
    return failures


def validate(context_path: Path, draft_path: Path) -> list[ValidationFailure]:
    context = read_json(context_path)
    draft = read_json(draft_path)
    failures: list[ValidationFailure] = []
    failures.extend(validate_policy(draft))
    failures.extend(validate_claims(draft, context))
    failures.extend(validate_gaps(draft, context))
    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 8 constrained impact draft artifact.")
    parser.add_argument("--context", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_context.v2.enriched.json")
    parser.add_argument("--draft", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_draft.v1.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate(args.context, args.draft)
    if failures:
        print("[gate8:validate] FAILED")
        for failure in failures:
            print(f"[gate8:validate] {failure.check}: {failure.detail}")
        raise SystemExit(1)
    print("[gate8:validate] OK")
    print(f"[gate8:validate] context={args.context}")
    print(f"[gate8:validate] draft={args.draft}")


if __name__ == "__main__":
    main()
