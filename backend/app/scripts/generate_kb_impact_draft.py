from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import relpath, repo_root


@dataclass(frozen=True)
class DraftClaim:
    claim_id: str
    claim_type: str
    text: str
    evidence_ids: list[str]
    caveats: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DraftSection:
    section_id: str
    title: str
    status: str
    claims: list[DraftClaim] = field(default_factory=list)
    unresolved_gaps: list[str] = field(default_factory=list)
    reviewer_notes: str = ""


@dataclass(frozen=True)
class KBImpactDraft:
    artifact_type: str
    schema_version: str
    generated_utc: str
    draft_status: str
    source_context_path: str
    source_skeleton_path: str
    generation_policy: dict[str, Any]
    diagnostics: dict[str, Any]
    sections: list[DraftSection]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def evidence_ref(evidence_ids: list[str]) -> str:
    return "[evidence: " + ", ".join(sorted(evidence_ids)) + "]"


def item_label(item: dict[str, Any]) -> str:
    return " / ".join(
        filter(
            None,
            [
                item.get("kb_document_id"),
                f"bug {item.get('bug_patch_number')}" if item.get("bug_patch_number") else None,
                item.get("product"),
                item.get("category"),
            ],
        )
    )


def visual_caveat_for_items(items: list[dict[str, Any]]) -> list[str]:
    if any((item.get("pdf_context_flags") or {}).get("has_images") for item in items):
        return ["One or more cited PFDS evidence items are image-bearing; reviewer visual inspection is required before final impact conclusions."]
    return []


def build_scope_section(context: dict[str, Any]) -> DraftSection:
    diagnostics = context.get("diagnostics", {})
    evidence_ids = sorted(item.get("evidence_id") for item in context.get("evidence_items", []) if item.get("evidence_id"))
    text = (
        "This draft is based on the assembled KB/PFDS evidence packet containing "
        f"{diagnostics.get('assembled_evidence_items', 0)} evidence items grouped into "
        f"{diagnostics.get('evidence_groups', 0)} evidence groups. {evidence_ref(evidence_ids)}"
    )
    return DraftSection(
        section_id="scope_and_inputs",
        title="Scope and Inputs",
        status="DRAFT_CITATION_BOUND_NOT_REVIEWED",
        claims=[
            DraftClaim(
                claim_id="scope_and_inputs_001",
                claim_type="source_scope",
                text=text,
                evidence_ids=evidence_ids,
                caveats=visual_caveat_for_items(context.get("evidence_items", [])),
            )
        ],
    )


def build_evidence_group_section(context: dict[str, Any]) -> DraftSection:
    items_by_id = {item.get("evidence_id"): item for item in context.get("evidence_items", [])}
    claims: list[DraftClaim] = []
    for index, group in enumerate(context.get("evidence_groups", []), start=1):
        evidence_ids = [evidence_id for evidence_id in group.get("evidence_ids", []) if evidence_id in items_by_id]
        group_items = [items_by_id[evidence_id] for evidence_id in evidence_ids]
        text = (
            f"Evidence group {group.get('group_key')} contains {group.get('evidence_count')} cited item(s) for "
            f"{group.get('product')} / {group.get('category')} under bug/patch {group.get('bug_patch_number')}. "
            f"{evidence_ref(evidence_ids)}"
        )
        claims.append(
            DraftClaim(
                claim_id=f"evidence_group_{index:03d}",
                claim_type="evidence_group_inventory",
                text=text,
                evidence_ids=evidence_ids,
                caveats=visual_caveat_for_items(group_items),
            )
        )
    return DraftSection(
        section_id="evidence_groups",
        title="Evidence Groups",
        status="DRAFT_CITATION_BOUND_NOT_REVIEWED",
        claims=claims,
    )


def build_product_sections(context: dict[str, Any]) -> list[DraftSection]:
    items_by_product: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in context.get("evidence_items", []):
        items_by_product[item.get("product") or "UNKNOWN_PRODUCT"].append(item)

    sections: list[DraftSection] = []
    for index, (product, items) in enumerate(sorted(items_by_product.items()), start=1):
        categories = Counter(item.get("category") or "UNKNOWN_CATEGORY" for item in items)
        bug_patch_numbers = sorted({item.get("bug_patch_number") for item in items if item.get("bug_patch_number")})
        evidence_ids = sorted({item.get("evidence_id") for item in items if item.get("evidence_id")})
        category_text = ", ".join(f"{category} ({count})" for category, count in sorted(categories.items()))
        text = (
            f"Retrieved evidence for {product} is concentrated in these category areas: {category_text}. "
            f"The cited bug/patch references are {', '.join(bug_patch_numbers)}. {evidence_ref(evidence_ids)}"
        )
        sections.append(
            DraftSection(
                section_id=f"impacted_product_area_{index:02d}",
                title=f"Impacted Product Area: {product}",
                status="DRAFT_CITATION_BOUND_NOT_REVIEWED",
                claims=[
                    DraftClaim(
                        claim_id=f"impacted_product_area_{index:02d}_001",
                        claim_type="retrieved_evidence_product_area",
                        text=text,
                        evidence_ids=evidence_ids,
                        caveats=visual_caveat_for_items(items),
                    )
                ],
            )
        )
    return sections


def build_unresolved_gaps_section(context: dict[str, Any]) -> DraftSection:
    exceptions = (context.get("evidence_exception_context") or {}).get("high_severity_exceptions", [])
    unresolved_gaps: list[str] = []
    claims: list[DraftClaim] = []
    for exception in exceptions:
        unresolved_gaps.append(
            "Missing PFDS evidence remains unresolved for "
            f"{exception.get('kb_document_id')} bug/patch {exception.get('bug_patch_number')} "
            f"({exception.get('product')} / {exception.get('category')}): {exception.get('description')}"
        )
    if unresolved_gaps:
        claims.append(
            DraftClaim(
                claim_id="unresolved_evidence_gaps_001",
                claim_type="missing_evidence_inventory",
                text=(
                    f"There are {len(unresolved_gaps)} high-severity missing-PFDS evidence exceptions. "
                    "These gaps are listed for reviewer follow-up and are not used as standalone impact conclusions."
                ),
                evidence_ids=[],
                caveats=["No impact claim is made from missing evidence alone."],
            )
        )
    return DraftSection(
        section_id="unresolved_evidence_gaps",
        title="Unresolved Evidence Gaps",
        status="DRAFT_GAP_INVENTORY_NOT_REVIEWED",
        claims=claims,
        unresolved_gaps=unresolved_gaps,
    )


def build_assumptions_section() -> DraftSection:
    return DraftSection(
        section_id="assumptions",
        title="Assumptions",
        status="EMPTY_REVIEWER_REQUIRED",
        reviewer_notes="No assumptions were generated. Reviewer-authored assumptions may be added later.",
    )


def build_reviewer_notes_section() -> DraftSection:
    return DraftSection(
        section_id="reviewer_notes",
        title="Reviewer Notes",
        status="EMPTY_REVIEWER_REQUIRED",
        reviewer_notes="Reserved for reviewer-authored notes.",
    )


def build_draft_status_section() -> DraftSection:
    return DraftSection(
        section_id="draft_status",
        title="Draft Status",
        status="DRAFT_NOT_REVIEWED_NOT_FINAL",
        claims=[
            DraftClaim(
                claim_id="draft_status_001",
                claim_type="draft_status",
                text="This artifact is a citation-bound draft generated from retrieved evidence. It is not reviewed, not final, and not a finalized business finding.",
                evidence_ids=[],
                caveats=["Reviewer validation is required before any impact statement can be finalized."],
            )
        ],
    )


def build_draft(context_path: Path, skeleton_path: Path) -> KBImpactDraft:
    root = repo_root()
    context = read_json(context_path)
    skeleton = read_json(skeleton_path)
    sections: list[DraftSection] = [
        build_scope_section(context),
        build_evidence_group_section(context),
        *build_product_sections(context),
        build_assumptions_section(),
        build_unresolved_gaps_section(context),
        build_reviewer_notes_section(),
        build_draft_status_section(),
    ]
    claim_count = sum(len(section.claims) for section in sections)
    evidence_citation_count = sum(len(claim.evidence_ids) for section in sections for claim in section.claims)
    unresolved_gap_count = sum(len(section.unresolved_gaps) for section in sections)
    image_bearing_cited_evidence = len(
        {
            item.get("evidence_id")
            for item in context.get("evidence_items", [])
            if (item.get("pdf_context_flags") or {}).get("has_images") and item.get("evidence_id")
        }
    )

    return KBImpactDraft(
        artifact_type="kb_impact_draft",
        schema_version="kb_impact_draft.v1",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        draft_status="DRAFT_CITATION_BOUND_NOT_REVIEWED_NOT_FINAL",
        source_context_path=relpath(context_path, root),
        source_skeleton_path=relpath(skeleton_path, root),
        generation_policy={
            "llm_used": False,
            "generator": "deterministic_template_v1",
            "external_claims_allowed": False,
            "claims_require_evidence_ids": True,
            "missing_evidence_can_create_impact_claims": False,
            "image_bearing_evidence_requires_visual_review_caveat": True,
            "draft_review_status": "NOT_REVIEWED_NOT_FINAL",
        },
        diagnostics={
            "source_skeleton_sections": len(skeleton.get("sections", [])),
            "draft_sections": len(sections),
            "draft_claims": claim_count,
            "evidence_citation_count": evidence_citation_count,
            "unresolved_gap_count": unresolved_gap_count,
            "image_bearing_cited_evidence": image_bearing_cited_evidence,
        },
        sections=sections,
    )


def write_draft(draft: KBImpactDraft, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(draft), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Generate a constrained citation-bound impact draft from enriched KB impact context.")
    parser.add_argument("--context", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_context.v2.enriched.json")
    parser.add_argument("--skeleton", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_draft_skeleton.v1.json")
    parser.add_argument("--output", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_draft.v1.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    draft = build_draft(args.context, args.skeleton)
    write_draft(draft, args.output)
    print(f"Wrote KB impact draft: {args.output}")
    print(f"Draft status: {draft.draft_status}")
    print(f"Draft sections: {draft.diagnostics['draft_sections']}")
    print(f"Draft claims: {draft.diagnostics['draft_claims']}")
    print(f"Unresolved gaps: {draft.diagnostics['unresolved_gap_count']}")


if __name__ == "__main__":
    main()
