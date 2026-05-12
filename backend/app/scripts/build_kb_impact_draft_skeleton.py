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
class DraftSection:
    section_id: str
    title: str
    status: str
    instructions: str
    evidence_ids: list[str] = field(default_factory=list)
    content: str = ""


@dataclass(frozen=True)
class KBImpactDraftSkeleton:
    artifact_type: str
    schema_version: str
    generated_utc: str
    source_context_path: str
    generation_policy: dict[str, Any]
    skeleton_status: str
    diagnostics: dict[str, Any]
    sections: list[DraftSection]


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def build_product_sections(items: list[dict[str, Any]]) -> list[DraftSection]:
    evidence_by_product: dict[str, list[str]] = defaultdict(list)
    for item in items:
        product = item.get("product") or "UNKNOWN_PRODUCT"
        evidence_by_product[product].append(item["evidence_id"])

    sections: list[DraftSection] = []
    for index, (product, evidence_ids) in enumerate(sorted(evidence_by_product.items()), start=1):
        sections.append(
            DraftSection(
                section_id=f"impacted_product_area_{index:02d}",
                title=f"Impacted Product Area: {product}",
                status="EMPTY_NO_GENERATED_CLAIMS",
                instructions="Reviewer may use cited evidence IDs to draft impact notes later. Do not infer conclusions in this skeleton.",
                evidence_ids=sorted(set(evidence_ids)),
            )
        )
    return sections


def build_skeleton(source_context_path: Path) -> KBImpactDraftSkeleton:
    root = repo_root()
    context = read_json(source_context_path)
    items = context.get("evidence_items", [])
    groups = context.get("evidence_groups", [])
    exception_context = context.get("evidence_exception_context", {})
    product_counts = Counter(item.get("product") or "UNKNOWN_PRODUCT" for item in items)

    all_evidence_ids = sorted({item.get("evidence_id") for item in items if item.get("evidence_id")})
    high_exception_ids = [exception.get("bug_patch_number") for exception in exception_context.get("high_severity_exceptions", [])]

    sections: list[DraftSection] = [
        DraftSection(
            section_id="scope_and_inputs",
            title="Scope and Inputs",
            status="STRUCTURE_ONLY_NO_GENERATED_CLAIMS",
            instructions="List source artifacts and retrieval/evaluation inputs. Do not summarize business impact.",
            evidence_ids=[],
        ),
        DraftSection(
            section_id="evidence_groups",
            title="Evidence Groups",
            status="STRUCTURE_ONLY_NO_GENERATED_CLAIMS",
            instructions="Reference evidence groups and evidence IDs. Do not interpret them as impact conclusions.",
            evidence_ids=all_evidence_ids,
        ),
    ]
    sections.extend(build_product_sections(items))
    sections.extend(
        [
            DraftSection(
                section_id="assumptions",
                title="Assumptions",
                status="EMPTY_NO_GENERATED_CLAIMS",
                instructions="Reserved for human-reviewed assumptions. Leave empty until explicitly reviewed.",
                evidence_ids=[],
            ),
            DraftSection(
                section_id="unresolved_evidence_gaps",
                title="Unresolved Evidence Gaps",
                status="STRUCTURE_ONLY_NO_GENERATED_CLAIMS",
                instructions="Reference known missing or exception evidence. Do not infer impact from missing evidence alone.",
                evidence_ids=[] ,
                content="High-severity missing PFDS bug/patch references: " + ", ".join(sorted(filter(None, high_exception_ids))),
            ),
            DraftSection(
                section_id="reviewer_notes",
                title="Reviewer Notes",
                status="EMPTY_NO_GENERATED_CLAIMS",
                instructions="Reserved for reviewer-authored notes.",
                evidence_ids=[],
            ),
            DraftSection(
                section_id="no_generated_conclusion_status",
                title="No Generated Conclusion Status",
                status="NO_GENERATED_CONCLUSIONS",
                instructions="This skeleton intentionally contains no generated impact conclusions.",
                evidence_ids=[],
                content="No impact conclusions have been generated. This artifact is a structured container over cited evidence only.",
            ),
        ]
    )

    return KBImpactDraftSkeleton(
        artifact_type="kb_impact_draft_skeleton",
        schema_version="kb_impact_draft_skeleton.v1",
        generated_utc=datetime.now(timezone.utc).isoformat(),
        source_context_path=relpath(source_context_path, root),
        generation_policy={
            "llm_used": False,
            "impact_claims_generated": False,
            "narrative_generated": False,
            "allowed_use": "Structure-only draft container for later reviewer-controlled impact drafting.",
            "prohibited_use": "Do not treat this skeleton as impact analysis or generated conclusions.",
        },
        skeleton_status="STRUCTURE_ONLY_NO_GENERATED_CLAIMS",
        diagnostics={
            "evidence_items": len(items),
            "evidence_groups": len(groups),
            "product_count": len(product_counts),
            "section_count": len(sections),
            "high_severity_exception_count": len(high_exception_ids),
        },
        sections=sections,
    )


def write_skeleton(skeleton: KBImpactDraftSkeleton, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(asdict(skeleton), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build Gate 7 structure-only impact draft skeleton from enriched context.")
    parser.add_argument("--source-context", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_context.v2.enriched.json")
    parser.add_argument("--output", type=Path, default=root / "kbs" / "impact_context" / "kb_impact_draft_skeleton.v1.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    skeleton = build_skeleton(args.source_context)
    write_skeleton(skeleton, args.output)
    print(f"Wrote KB impact draft skeleton: {args.output}")
    print(f"Skeleton status: {skeleton.skeleton_status}")
    print(f"Sections: {skeleton.diagnostics['section_count']}")
    print(f"Evidence items cited: {skeleton.diagnostics['evidence_items']}")


if __name__ == "__main__":
    main()
