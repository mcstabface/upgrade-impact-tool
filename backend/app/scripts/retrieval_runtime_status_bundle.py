from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.retrieval_runtime_adapter_boundary import (
    DEFAULT_RUNTIME_BOUNDARY_REPORT,
    build_runtime_boundary_report,
    write_runtime_boundary_report,
)
from app.scripts.retrieval_runtime_health_surface import (
    DEFAULT_RUNTIME_HEALTH_REPORT,
    build_runtime_health_surface_report,
    write_runtime_health_surface_report,
)
from app.scripts.retrieval_runtime_operator_status_export import (
    DEFAULT_OPERATOR_STATUS_EXPORT,
    build_operator_status,
    write_operator_status,
)


DEFAULT_RUNTIME_STATUS_BUNDLE = "kbs/retrieval/kb_retrieval_runtime_status_bundle.v1.json"


@dataclass(frozen=True)
class RetrievalRuntimeStatusBundle:
    report_version: str
    status: str
    boundary_status: str
    health_status: str
    operator_action_required: str
    live_adapter: str
    bm25_authoritative: bool
    semantic_retrieval_enabled: bool
    hybrid_merge_enabled: bool
    fail_closed: bool
    boundary_report: str
    health_report: str
    operator_status_export: str
    errors: list[str]


def _relative(path: Path) -> str:
    root = repo_root()
    return str(path.relative_to(root)) if path.is_relative_to(root) else str(path)


def build_status_bundle(
    *,
    enablement_report_path: Path,
    boundary_report_path: Path,
    health_report_path: Path,
    operator_status_path: Path,
) -> RetrievalRuntimeStatusBundle:
    boundary_report = build_runtime_boundary_report(
        enablement_report_path=enablement_report_path,
        requested_adapter="bm25_authoritative",
    )
    write_runtime_boundary_report(boundary_report_path, boundary_report)

    health_report = build_runtime_health_surface_report(boundary_report_path=boundary_report_path)
    write_runtime_health_surface_report(health_report_path, health_report)

    operator_status = build_operator_status(health_report_path=boundary_report_path)
    write_operator_status(operator_status_path, operator_status)

    errors: list[str] = []
    if boundary_report.status != "RETRIEVAL_RUNTIME_BOUNDARY_READY":
        errors.append(f"boundary_status={boundary_report.status}")
    if health_report.status != "RETRIEVAL_RUNTIME_HEALTHY":
        errors.append(f"health_status={health_report.status}")
    if operator_status.action_required != "none":
        errors.append(f"operator_action_required={operator_status.action_required}")

    status = "RETRIEVAL_RUNTIME_STATUS_BUNDLE_READY" if not errors else "RETRIEVAL_RUNTIME_STATUS_BUNDLE_UNHEALTHY"

    return RetrievalRuntimeStatusBundle(
        report_version="1",
        status=status,
        boundary_status=boundary_report.status,
        health_status=health_report.status,
        operator_action_required=operator_status.action_required,
        live_adapter=operator_status.live_adapter,
        bm25_authoritative=operator_status.bm25_authoritative,
        semantic_retrieval_enabled=operator_status.semantic_retrieval_enabled,
        hybrid_merge_enabled=operator_status.hybrid_merge_enabled,
        fail_closed=operator_status.fail_closed,
        boundary_report=_relative(boundary_report_path),
        health_report=_relative(health_report_path),
        operator_status_export=_relative(operator_status_path),
        errors=errors,
    )


def write_status_bundle(path: Path, bundle: RetrievalRuntimeStatusBundle) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(bundle), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Build retrieval runtime status bundle.")
    parser.add_argument("--enablement-report", type=Path, default=root / "kbs/retrieval/kb_production_semantic_retrieval_enablement_gate.v1.json")
    parser.add_argument("--boundary-report", type=Path, default=root / DEFAULT_RUNTIME_BOUNDARY_REPORT)
    parser.add_argument("--health-report", type=Path, default=root / DEFAULT_RUNTIME_HEALTH_REPORT)
    parser.add_argument("--operator-status", type=Path, default=root / DEFAULT_OPERATOR_STATUS_EXPORT)
    parser.add_argument("--output", type=Path, default=root / DEFAULT_RUNTIME_STATUS_BUNDLE)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    bundle = build_status_bundle(
        enablement_report_path=args.enablement_report,
        boundary_report_path=args.boundary_report,
        health_report_path=args.health_report,
        operator_status_path=args.operator_status,
    )
    write_status_bundle(args.output, bundle)
    print(f"[gate20f:status-bundle] Wrote status bundle: {args.output}")
    print(f"[gate20f:status-bundle] status={bundle.status}")
    print(f"[gate20f:status-bundle] boundary_status={bundle.boundary_status}")
    print(f"[gate20f:status-bundle] health_status={bundle.health_status}")
    print(f"[gate20f:status-bundle] operator_action_required={bundle.operator_action_required}")
    print(f"[gate20f:status-bundle] live_adapter={bundle.live_adapter}")
    print(f"[gate20f:status-bundle] semantic_retrieval_enabled={'true' if bundle.semantic_retrieval_enabled else 'false'}")


if __name__ == "__main__":
    main()
