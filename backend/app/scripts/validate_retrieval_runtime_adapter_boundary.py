from __future__ import annotations

import copy
import json
import tempfile
from pathlib import Path
from typing import Any

from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.production_semantic_retrieval_enablement_gate import (
    DEFAULT_ENABLEMENT_REPORT,
    build_enablement_gate_report,
    write_enablement_gate_report,
)
from app.scripts.retrieval_runtime_adapter_boundary import (
    build_runtime_boundary_report,
    read_json,
    write_runtime_boundary_report,
)


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def ensure_ready_enablement_report() -> Path:
    root = repo_root()
    enablement = root / DEFAULT_ENABLEMENT_REPORT
    if not enablement.exists():
        write_enablement_gate_report(
            enablement,
            build_enablement_gate_report(
                citation_preservation_path=root / "kbs" / "retrieval" / "kb_hybrid_retrieval_citation_preservation.v1.json"
            ),
        )
    return enablement


def assert_default_selects_bm25() -> None:
    enablement = ensure_ready_enablement_report()
    report = build_runtime_boundary_report(enablement_report_path=enablement, requested_adapter="bm25_authoritative")
    if report.status != "RETRIEVAL_RUNTIME_BOUNDARY_READY":
        raise AssertionError(f"Unexpected boundary status: {report.status}")
    if report.live_adapter != "bm25_authoritative":
        raise AssertionError(f"Unexpected live adapter: {report.live_adapter}")
    if report.selection.status != "SELECTED":
        raise AssertionError(f"Expected selected status, got: {report.selection.status}")
    if report.selection.selected_adapter != "bm25_authoritative":
        raise AssertionError(f"Expected bm25 selected, got: {report.selection.selected_adapter}")
    if report.semantic_retrieval_enabled is not False:
        raise AssertionError("Semantic retrieval must remain disabled")
    if report.hybrid_merge_enabled is not False:
        raise AssertionError("Hybrid merge must remain disabled")
    if report.bm25_authoritative is not True:
        raise AssertionError("BM25 must remain authoritative")
    if report.fail_closed is not True:
        raise AssertionError("Boundary must fail closed")
    with tempfile.TemporaryDirectory() as temp_dir:
        output = Path(temp_dir) / "runtime_boundary.json"
        write_runtime_boundary_report(output, report)
        persisted = read_json(output)
        if persisted.get("semantic_retrieval_enabled") is not False:
            raise AssertionError("Persisted boundary must keep semantic retrieval disabled")


def assert_disabled_adapters_refuse() -> None:
    enablement = ensure_ready_enablement_report()
    for adapter_name in ("semantic_vector", "hybrid_retrieval"):
        report = build_runtime_boundary_report(enablement_report_path=enablement, requested_adapter=adapter_name)
        if report.status != "RETRIEVAL_RUNTIME_BOUNDARY_REFUSED":
            raise AssertionError(f"Disabled adapter must refuse: {adapter_name}")
        if report.selection.reason != "REQUESTED_ADAPTER_DISABLED":
            raise AssertionError(f"Unexpected disabled reason for {adapter_name}: {report.selection.reason}")
        if report.selection.selected_adapter != "bm25_authoritative":
            raise AssertionError("Disabled adapter refusal should preserve bm25 fallback identity")
        if report.selection.semantic_retrieval_enabled is not False:
            raise AssertionError("Disabled adapter must not enable semantic retrieval")


def assert_unsupported_adapter_refuses() -> None:
    enablement = ensure_ready_enablement_report()
    report = build_runtime_boundary_report(enablement_report_path=enablement, requested_adapter="magic_agent_mode")
    if report.status != "RETRIEVAL_RUNTIME_BOUNDARY_REFUSED":
        raise AssertionError("Unsupported adapter must refuse")
    if report.selection.reason != "UNSUPPORTED_ADAPTER":
        raise AssertionError(f"Unexpected unsupported reason: {report.selection.reason}")
    if not report.selection.errors:
        raise AssertionError("Unsupported adapter refusal must include errors")


def assert_invalid_enablement_report_refuses() -> None:
    source = read_json(ensure_ready_enablement_report())
    bad = copy.deepcopy(source)
    bad["production_semantic_retrieval_enabled"] = True
    bad["status"] = "PRODUCTION_SEMANTIC_RETRIEVAL_ENABLEMENT_BLOCKED"
    with tempfile.TemporaryDirectory() as temp_dir:
        bad_path = Path(temp_dir) / "bad_enablement.json"
        write_json(bad_path, bad)
        report = build_runtime_boundary_report(enablement_report_path=bad_path, requested_adapter="bm25_authoritative")
        if report.status != "RETRIEVAL_RUNTIME_BOUNDARY_REFUSED":
            raise AssertionError(f"Expected refused boundary, got: {report.status}")
        if report.selection.reason != "ENABLEMENT_REPORT_INVALID":
            raise AssertionError(f"Unexpected invalid enablement reason: {report.selection.reason}")
        if report.selection.semantic_retrieval_enabled is not False:
            raise AssertionError("Invalid enablement must not enable semantic retrieval")


def main() -> None:
    assert_default_selects_bm25()
    assert_disabled_adapters_refuse()
    assert_unsupported_adapter_refuses()
    assert_invalid_enablement_report_refuses()
    print("[gate20a:runtime-boundary] OK")
    print("[gate20a:runtime-boundary] default_adapter=bm25_authoritative")
    print("[gate20a:runtime-boundary] disabled_adapters=refused")
    print("[gate20a:runtime-boundary] unsupported_adapter=fail_closed")
    print("[gate20a:runtime-boundary] semantic_retrieval_enabled=false")


if __name__ == "__main__":
    main()
