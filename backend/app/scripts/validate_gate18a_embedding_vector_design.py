from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


@dataclass(frozen=True)
class ValidationFailure:
    check: str
    detail: str


def read_text(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"Required design spec not found: {path}")
    return path.read_text(encoding="utf-8")


def validate_design_spec(path: Path) -> list[ValidationFailure]:
    text = read_text(path)
    failures: list[ValidationFailure] = []

    required_fragments = [
        "Gate 18A Embedding Manifest Vector Store Design Spec",
        "This gate is design-only",
        "does not call an embedding model",
        "does not create vectors",
        "does not replace BM25 retrieval",
        "kbs/retrieval/kb_embedding_manifest.v1.json",
        "kbs/retrieval/kb_vectors.v1.jsonl",
        "kbs/retrieval/kb_vector_index.v1.json",
        "chunk_text_with_stable_metadata_prefix_v1",
        "sha256(model|dimensions|input_policy|chunk_id|chunk_text_sha256)",
        "bm25_only",
        "vector_only",
        "hybrid_bm25_vector",
        "Gate 18B — Embedding Manifest Skeleton and Validator",
    ]
    for fragment in required_fragments:
        if fragment not in text:
            failures.append(ValidationFailure("required_fragment", f"Missing required fragment: {fragment!r}"))

    required_sections = [
        "## Purpose",
        "## Baseline",
        "## Design Goals",
        "## Non-Goals",
        "## Proposed Embedding Manifest",
        "## Chunk Record Contract",
        "## Embedding Input Policy",
        "## Cache Key Policy",
        "## Vector Store Design",
        "## Retrieval Integration Policy",
        "## Evaluation Requirements",
        "## Safety and Governance Requirements",
        "## Required Test Matrix Before Implementation",
        "## Recommended Next Gate",
    ]
    for section in required_sections:
        if section not in text:
            failures.append(ValidationFailure("required_section", f"Missing required section: {section!r}"))

    forbidden_fragments = [
        "replace BM25",
        "run implicitly during review mutation",
        "run implicitly during draft generation",
        "finalization_allowed = true",
    ]
    text_lower = text.lower()
    for fragment in forbidden_fragments:
        if fragment.lower() in text_lower:
            failures.append(ValidationFailure("forbidden_fragment", f"Forbidden design claim found: {fragment!r}"))

    return failures


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Validate Gate 18A embedding manifest and vector store design spec.")
    parser.add_argument(
        "--spec",
        type=Path,
        default=root / "docs" / "checkpoints" / "Gate 18A Embedding Manifest Vector Store Design Spec.md",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    failures = validate_design_spec(args.spec)
    if failures:
        print("[gate18a:design] FAILED")
        for failure in failures:
            print(f"[gate18a:design] {failure.check}: {failure.detail}")
        raise SystemExit(1)
    print("[gate18a:design] OK")
    print("[gate18a:design] embedding_manifest=specified_not_implemented")
    print("[gate18a:design] vector_store=specified_not_created")
    print("[gate18a:design] bm25=preserved")
    print("[gate18a:design] embedding_calls=forbidden")


if __name__ == "__main__":
    main()
