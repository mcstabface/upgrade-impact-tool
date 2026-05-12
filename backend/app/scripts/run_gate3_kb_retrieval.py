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


def build_steps(smoke_query: str) -> list[PipelineStep]:
    return [
        PipelineStep(
            label="Build KB chunk lexical index",
            module="app.scripts.build_kb_chunk_lexical_index",
            args=[],
        ),
        PipelineStep(
            label="Run KB chunk retrieval smoke query",
            module="app.scripts.query_kb_chunks",
            args=[smoke_query, "--top-k", "5"],
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
    print(f"[gate3] {step.label}")
    print(f"[gate3]   {' '.join(command)}")

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
        description="Run the Gate 3 KB PFDS lexical retrieval index and smoke-query pipeline."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the pipeline commands without running them.",
    )
    parser.add_argument(
        "--smoke-query",
        default=DEFAULT_SMOKE_QUERY,
        help="Smoke query to run after building the lexical index.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    repository_root = repo_root()

    print("[gate3] Starting KB retrieval pipeline")
    print(f"[gate3] Repository root: {repository_root}")

    for step in build_steps(args.smoke_query):
        run_step(step, dry_run=args.dry_run)

    if args.dry_run:
        print("[gate3] Dry run complete")
        return

    missing_outputs = verify_outputs(repository_root)
    if missing_outputs:
        print("[gate3] Pipeline completed, but expected outputs are missing:")
        for output in missing_outputs:
            print(f"[gate3]   missing: {output}")
        raise SystemExit(1)

    print("[gate3] Pipeline complete")
    print("[gate3] Outputs:")
    for output in EXPECTED_OUTPUTS:
        print(f"[gate3]   {output}")


if __name__ == "__main__":
    main()
