from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol

from app.scripts.extract_kb_source_manifest import repo_root


DEFAULT_FULL_TEXT_REQUEST_JSONL = "kbs/retrieval/kb_embedding_full_text_requests.v1.jsonl"
DEFAULT_PRECONDITION_REPORT = "kbs/retrieval/kb_embedding_submission_preconditions.v1.json"
DEFAULT_SUBMISSION_ADAPTER_REPORT = "kbs/retrieval/kb_embedding_submission_adapter_report.v1.json"
DEFAULT_RESPONSE_JSONL = "kbs/retrieval/kb_embedding_batch_responses.v1.jsonl"
DEFAULT_VECTOR_PATH = "kbs/retrieval/kb_vectors.v1.jsonl"
DEFAULT_VECTOR_INDEX_PATH = "kbs/retrieval/kb_vector_index.v1.json"


@dataclass(frozen=True)
class EmbeddingSubmissionRequest:
    request_jsonl_path: str
    precondition_report_path: str
    adapter_name: str
    dry_run_only: bool = True


@dataclass(frozen=True)
class EmbeddingSubmissionResult:
    status: str
    adapter_name: str
    reason: str
    request_count: int
    would_submit: bool
    real_submission_allowed: bool
    response_jsonl_path: str
    vector_jsonl_path: str
    vector_index_path: str
    errors: list[str] = field(default_factory=list)


class EmbeddingSubmissionAdapter(Protocol):
    adapter_name: str

    def submit(self, request: EmbeddingSubmissionRequest) -> EmbeddingSubmissionResult:
        """Submit or refuse an embedding batch request."""


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def read_jsonl_count(path: Path) -> int:
    count = 0
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if not isinstance(payload, dict):
            raise ValueError(f"Expected JSON object row: {path}")
        count += 1
    return count


def validate_submission_preconditions(precondition_report_path: Path) -> list[str]:
    errors: list[str] = []
    if not precondition_report_path.exists():
        return [f"precondition report not found: {precondition_report_path}"]
    report = read_json(precondition_report_path)
    if report.get("status") != "PRECONDITIONS_READY_DRY_RUN_ONLY":
        errors.append(f"precondition status is not ready dry-run only: {report.get('status')}")
    if report.get("failed_count") != 0:
        errors.append(f"precondition failed_count must be 0: {report.get('failed_count')}")
    if report.get("real_submission_allowed") is not False:
        errors.append("precondition report must keep real_submission_allowed false")
    if report.get("dry_run_only") is not True:
        errors.append("precondition report must keep dry_run_only true")
    if report.get("vectors_created") is not False:
        errors.append("precondition report must keep vectors_created false")
    return errors


class DisabledEmbeddingSubmissionAdapter:
    adapter_name = "disabled"

    def submit(self, request: EmbeddingSubmissionRequest) -> EmbeddingSubmissionResult:
        request_path = repo_root() / request.request_jsonl_path if not Path(request.request_jsonl_path).is_absolute() else Path(request.request_jsonl_path)
        precondition_path = (
            repo_root() / request.precondition_report_path
            if not Path(request.precondition_report_path).is_absolute()
            else Path(request.precondition_report_path)
        )
        errors: list[str] = []
        if not request_path.exists():
            errors.append(f"request JSONL not found: {request_path}")
            request_count = 0
        else:
            request_count = read_jsonl_count(request_path)
            if request_count <= 0:
                errors.append("request JSONL must contain at least one request")
        errors.extend(validate_submission_preconditions(precondition_path))
        reason = "DISABLED_ADAPTER_REFUSES_REAL_SUBMISSION"
        if errors:
            reason = "DISABLED_ADAPTER_INPUTS_INVALID"
        return EmbeddingSubmissionResult(
            status="REFUSED",
            adapter_name=self.adapter_name,
            reason=reason,
            request_count=request_count,
            would_submit=False,
            real_submission_allowed=False,
            response_jsonl_path=DEFAULT_RESPONSE_JSONL,
            vector_jsonl_path=DEFAULT_VECTOR_PATH,
            vector_index_path=DEFAULT_VECTOR_INDEX_PATH,
            errors=errors,
        )


def get_embedding_submission_adapter(adapter_name: str) -> EmbeddingSubmissionAdapter:
    if adapter_name == "disabled":
        return DisabledEmbeddingSubmissionAdapter()
    raise ValueError(f"Unsupported embedding submission adapter: {adapter_name}")


def build_submission_adapter_report(*, request_jsonl_path: Path, precondition_report_path: Path, adapter_name: str) -> EmbeddingSubmissionResult:
    root = repo_root()
    request_relative = str(request_jsonl_path.relative_to(root)) if request_jsonl_path.is_relative_to(root) else str(request_jsonl_path)
    precondition_relative = (
        str(precondition_report_path.relative_to(root)) if precondition_report_path.is_relative_to(root) else str(precondition_report_path)
    )
    adapter = get_embedding_submission_adapter(adapter_name)
    return adapter.submit(
        EmbeddingSubmissionRequest(
            request_jsonl_path=request_relative,
            precondition_report_path=precondition_relative,
            adapter_name=adapter_name,
            dry_run_only=True,
        )
    )


def write_submission_adapter_report(path: Path, result: EmbeddingSubmissionResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run Gate 18N disabled embedding submission adapter contract.")
    parser.add_argument("--request-jsonl", type=Path, default=root / DEFAULT_FULL_TEXT_REQUEST_JSONL)
    parser.add_argument("--precondition-report", type=Path, default=root / DEFAULT_PRECONDITION_REPORT)
    parser.add_argument("--adapter", default="disabled")
    parser.add_argument("--output", type=Path, default=root / DEFAULT_SUBMISSION_ADAPTER_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_submission_adapter_report(
        request_jsonl_path=args.request_jsonl,
        precondition_report_path=args.precondition_report,
        adapter_name=args.adapter,
    )
    write_submission_adapter_report(args.output, result)
    print(f"[gate18n:adapter] Wrote submission adapter report: {args.output}")
    print(f"[gate18n:adapter] status={result.status}")
    print(f"[gate18n:adapter] reason={result.reason}")
    print(f"[gate18n:adapter] request_count={result.request_count}")
    print("[gate18n:adapter] real_submission_allowed=false")
    print("[gate18n:adapter] vectors=not_created")


if __name__ == "__main__":
    main()
