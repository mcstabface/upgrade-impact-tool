from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root


@dataclass(frozen=True)
class PipelineStep:
    label: str
    module: str
    args: list[str]


DEFAULT_QUERY = "rates billing usage"
DEFAULT_FILTERED_PRODUCT = "Oracle Utilities Customer Care and Billing"


def build_steps(query: str, filtered_product: str) -> list[PipelineStep]:
    common_controls = [
        "--top-k",
        "5",
        "--max-chunks-per-child-pdf",
        "1",
        "--max-chunks-per-bug-patch",
        "1",
    ]
    filtered_controls = [
        "--top-k",
        "5",
        "--product",
        filtered_product,
        "--max-chunks-per-child-pdf",
        "1",
    ]

    return [
        PipelineStep(
            label="Build KB chunk lexical index",
            module="app.scripts.build_kb_chunk_lexical_index",
            args=[],
        ),
        PipelineStep(
            label="Run TF-IDF baseline query",
            module="app.scripts.query_kb_chunks",
            args=[query, "--ranker", "tfidf", *common_controls],
        ),
        PipelineStep(
            label="Run BM25 baseline query",
            module="app.scripts.query_kb_chunks",
            args=[query, "--ranker", "bm25", *common_controls],
        ),
        PipelineStep(
            label="Run filtered TF-IDF query",
            module="app.scripts.query_kb_chunks",
            args=[query, "--ranker", "tfidf", *filtered_controls],
        ),
        PipelineStep(
            label="Run filtered BM25 query",
            module="app.scripts.query_kb_chunks",
            args=[query, "--ranker", "bm25", *filtered_controls],
        ),
        PipelineStep(
            label="Validate KB retrieval artifacts",
            module="app.scripts.validate_gate3_kb_retrieval",
            args=[],
        ),
        PipelineStep(
            label="Validate KB retrieval diagnostics",
            module="app.scripts.validate_gate4_kb_retrieval_diagnostics",
            args=[],
        ),
        PipelineStep(
            label="Validate KB BM25 evaluation contexts",
            module="app.scripts.validate_gate5_kb_bm25_eval",
            args=[],
        ),
        PipelineStep(
            label="Write KB retrieval summary report",
            module="app.scripts.write_kb_retrieval_summary",
            args=[],
        ),
        PipelineStep(
            label="Write KB BM25 comparison summary report",
            module="app.scripts.write_kb_bm25_comparison_summary",
            args=[],
        ),
        PipelineStep(
            label="Run KB retrieval evaluation fixture",
            module="app.scripts.evaluate_kb_retrieval",
            args=[],
        ),
    ]


EXPECTED_OUTPUTS = [
    "kbs/indexes/kb_chunk_lexical_index.sqlite",
    "kbs/manifests/kb_chunk_lexical_index_manifest.json",
    "kbs/manifests/kb_retrieval_summary.md",
    "kbs/manifests/kb_bm25_comparison_summary.md",
    "kbs/manifests/kb_retrieval_eval_results.json",
    "kbs/manifests/kb_retrieval_eval_summary.md",
]


def run_step(step: PipelineStep, *, dry_run: bool) -> None:
    command = [sys.executable, "-m", step.module, *step.args]
    print(f"[gate5] {step.label}")
    print(f"[gate5]   {' '.join(command)}")

    if dry_run:
        return

    subprocess.run(command, check=True)


def verify_outputs(repository_root: Path) -> list[str]:
    missing: list[str] = []
    for output in EXPECTED_OUTPUTS:
        if not (repository_root / output).exists():
            missing.append(output)
    return missing


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Gate 5 deterministic BM25 ranking and retrieval evaluation checks.")
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument("--query", default=DEFAULT_QUERY, help="Query used for TF-IDF/BM25 comparison.")
    parser.add_argument("--filtered-product", default=DEFAULT_FILTERED_PRODUCT, help="Product filter for filtered comparison query.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate5] Starting KB BM25 evaluation pipeline")
    print(f"[gate5] Repository root: {repository_root}")

    for step in build_steps(args.query, args.filtered_product):
        run_step(step, dry_run=args.dry_run)

    if args.dry_run:
        print("[gate5] Dry run complete")
        return

    missing_outputs = verify_outputs(repository_root)
    if missing_outputs:
        print("[gate5] Pipeline completed, but expected outputs are missing:")
        for output in missing_outputs:
            print(f"[gate5]   missing: {output}")
        raise SystemExit(1)

    print("[gate5] Pipeline complete")
    print("[gate5] Outputs:")
    for output in EXPECTED_OUTPUTS:
        print(f"[gate5]   {output}")


if __name__ == "__main__":
    main()
