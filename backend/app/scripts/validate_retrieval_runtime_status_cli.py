from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.scripts.retrieval_runtime_status_cli import render_status_for_cli
from app.scripts.retrieval_runtime_operator_status_export import build_operator_status


def _assert(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def _write_boundary(path: Path, *, semantic_enabled: bool = False, fail_closed: bool = True) -> None:
    path.write_text(
        """{
  "bm25_authoritative": true,
  "fail_closed": %s,
  "hybrid_merge_enabled": false,
  "live_adapter": "bm25_authoritative",
  "report_version": "1",
  "selection": {
    "selected_adapter": "bm25_authoritative"
  },
  "semantic_retrieval_enabled": %s,
  "source_enablement_report": "kbs/retrieval/kb_production_semantic_retrieval_enablement_gate.v1.json",
  "status": "RETRIEVAL_RUNTIME_BOUNDARY_READY"
}
"""
        % ("true" if fail_closed else "false", "true" if semantic_enabled else "false"),
        encoding="utf-8",
    )


def test_text_output() -> None:
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "boundary.json"
        _write_boundary(path)
        status = build_operator_status(health_report_path=path)
        rendered = render_status_for_cli(status, output_format="text")
        _assert("# Retrieval Runtime Operator Status" in rendered, rendered)
        _assert("| live_adapter | `bm25_authoritative` |" in rendered, rendered)
        _assert("| semantic_retrieval_enabled | `false` |" in rendered, rendered)
        _assert("`none`" in rendered, rendered)


def test_json_output() -> None:
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "boundary.json"
        _write_boundary(path)
        status = build_operator_status(health_report_path=path)
        rendered = render_status_for_cli(status, output_format="json")
        payload = json.loads(rendered)
        _assert(payload["status"] == "RETRIEVAL_RUNTIME_HEALTHY", payload)
        _assert(payload["live_adapter"] == "bm25_authoritative", payload)
        _assert(payload["semantic_retrieval_enabled"] is False, payload)
        _assert(payload["action_required"] == "none", payload)


def test_invalid_output_format_fails() -> None:
    with TemporaryDirectory() as tmp:
        path = Path(tmp) / "boundary.json"
        _write_boundary(path)
        status = build_operator_status(health_report_path=path)
        try:
            render_status_for_cli(status, output_format="yaml")
        except ValueError as exc:
            _assert("unsupported output format" in str(exc), str(exc))
            return
        raise AssertionError("invalid output format did not fail")


def run_validation() -> None:
    test_text_output()
    test_json_output()
    test_invalid_output_format_fails()
    print("[gate20d:status-cli] OK")
    print("[gate20d:status-cli] text_output=pass")
    print("[gate20d:status-cli] json_output=pass")
    print("[gate20d:status-cli] invalid_format=fail_closed")
    print("[gate20d:status-cli] live_adapter=bm25_authoritative")
    print("[gate20d:status-cli] semantic_retrieval_enabled=false")


if __name__ == "__main__":
    run_validation()
