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


DEFAULT_SMOKE_QUERY = "rates billing usage"
DEFAULT_FILTERED_QUERY = "rates billing usage"
DEFAULT_FILTERED_PRODUCT = "Oracle Utilities Customer Care and Billing"


def build_steps(smoke_query: str, filtered_query: str, filtered_product: str) -> list[PipelineStep]:
    return [
        PipelineStep(
            label="Build KB chunk lexical index",
            module="app.scripts.build_kb_chunk_lexical_index",
            args=[],
        ),
        PipelineStep(
            label="Run diagnostic smoke query with source diversity controls",
            module="app.scripts.query_kb_chunks",
            args=[
                smoke_query,
                "--top-k",
                "5",
                "--max-chunks-per-child-pdf",
                "1",
                "--max-chunks-per-bug-patch",
                "1",
            ],
        ),
        PipelineStep(
            label="Run filtered diagnostic smoke query",
            module="app.scripts.query_kb_chunks",
            args=[
                filtered_query,
                "--top-k",
                "5",
                "--product",
                filtered_product,
                "--max-chunks-per-child-pdf",
                "1",
            ],
        ),
        PipelineStep(
            label="Validate KB retrieval artifacts",
            module="app.scripts.validate_gate3_kb_retrieval",
            args=[],
        ),
        PipelineStep(
            label="Write KB retrieval summary report",
            module="app.scripts.write_kb_retrieval_summary",
            args=[],
        ),
    ]


EXPECTED_OUTPUTS = [
    "kbs/indexes/kb_chunk_lexical_index.sqlite",
    "kbs/manifests/kb_chunk_lexical_index_manifest.json",
    "kbs/manifests/kb_retrieval_summary.md",
]


def run_step(step: PipelineStep, *, dry_run: bool) -> None:
    command = [sys.executable, "-m", step.module, *step.args]
    print(f"[gate4] {step.label}")
    print(f"[gate4]   {' '.join(command)}")

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
    parser = argparse.ArgumentParser(
        description="Run Gate 4 KB PFDS retrieval diagnostics and controls smoke checks."
    )
    parser.add_argument("--dry-run", action="store_true", help="Print commands without running them.")
    parser.add_argument("--smoke-query", default=DEFAULT_SMOKE_QUERY, help="Unfiltered diagnostic smoke query.")
    parser.add_argument("--filtered-query", default=DEFAULT_FILTERED_QUERY, help="Filtered diagnostic smoke query.")
    parser.add_argument("--filtered-product", default=DEFAULT_FILTERED_PRODUCT, help="Product filter for filtered smoke query.")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate4] Starting KB retrieval diagnostics pipeline")
    print(f"[gate4] Repository root: {repository_root}")

    for step in build_steps(args.smoke_query, args.filtered_query, args.filtered_product):
        run_step(step, dry_run=args.dry_run)

    if args.dry_run:
        print("[gate4] Dry run complete")
        return

    missing_outputs = verify_outputs(repository_root)
    if missing_outputs:
        print("[gate4] Pipeline completed, but expected outputs are missing:")
        for output in missing_outputs:
            print(f"[gate4]   missing: {output}")
        raise SystemExit(1)

    print("[gate4] Pipeline complete")
    print("[gate4] Outputs:")
    for output in EXPECTED_OUTPUTS:
        print(f"[gate4]   {output}")


if __name__ == "__main__":
    main()
