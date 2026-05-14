from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.retrieval_runtime_adapter_boundary import DEFAULT_RUNTIME_BOUNDARY_REPORT
from app.scripts.retrieval_runtime_health_surface import ensure_boundary_report
from app.scripts.retrieval_runtime_operator_status_export import (
    RetrievalRuntimeOperatorStatus,
    build_operator_status,
    render_operator_status,
)


VALID_OUTPUT_FORMATS = {"text", "json"}


def status_to_json(status: RetrievalRuntimeOperatorStatus) -> str:
    return json.dumps(asdict(status), indent=2, sort_keys=True) + "\n"


def render_status_for_cli(status: RetrievalRuntimeOperatorStatus, *, output_format: str) -> str:
    if output_format == "text":
        return render_operator_status(status)
    if output_format == "json":
        return status_to_json(status)
    raise ValueError(f"unsupported output format: {output_format}")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Print retrieval runtime operator status.")
    parser.add_argument("--boundary-report", type=Path, default=root / DEFAULT_RUNTIME_BOUNDARY_REPORT)
    parser.add_argument("--enablement-report", type=Path, default=root / "kbs/retrieval/kb_production_semantic_retrieval_enablement_gate.v1.json")
    parser.add_argument("--format", choices=sorted(VALID_OUTPUT_FORMATS), default="text")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ensure_boundary_report(
        args.boundary_report,
        enablement_report_path=args.enablement_report,
        requested_adapter="bm25_authoritative",
    )
    status = build_operator_status(health_report_path=args.boundary_report)
    print(render_status_for_cli(status, output_format=args.format), end="")


if __name__ == "__main__":
    main()
