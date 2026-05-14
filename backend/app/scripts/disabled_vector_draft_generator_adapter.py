from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Protocol

from app.scripts.citation_bound_vector_draft_generation_contract import (
    DEFAULT_DRAFT_SKELETON_REPORT,
    build_generation_contract,
    write_generation_contract,
)
from app.scripts.extract_kb_source_manifest import repo_root
from app.scripts.gate18y_local_skeleton_fixture import ensure_local_skeleton_fixture


DEFAULT_GENERATION_CONTRACT_REPORT = "kbs/retrieval/kb_fixture_vector_draft_generation_contract.v1.json"
DEFAULT_DISABLED_GENERATOR_REPORT = "kbs/retrieval/kb_fixture_vector_disabled_generator.v1.json"
DEFAULT_DRAFT_OUTPUT_REPORT = "kbs/retrieval/kb_fixture_vector_generated_draft.v1.json"


@dataclass(frozen=True)
class VectorDraftGenerationRequest:
    generation_contract_path: str
    adapter_name: str = "disabled"


@dataclass(frozen=True)
class VectorDraftGenerationResult:
    status: str
    adapter_name: str
    reason: str
    generation_contract_path: str
    output_draft_path: str
    would_generate: bool
    draft_generation_enabled: bool
    llm_call_allowed: bool
    llm_call_performed: bool
    generated_text: str = ""
    errors: list[str] = field(default_factory=list)


class VectorDraftGeneratorAdapter(Protocol):
    adapter_name: str

    def generate(self, request: VectorDraftGenerationRequest) -> VectorDraftGenerationResult:
        """Generate or refuse a vector-grounded draft."""


def read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"Expected JSON object: {path}")
    return payload


def ensure_generation_contract(contract_path: Path) -> None:
    if contract_path.exists():
        return
    root = repo_root()
    skeleton_path = root / DEFAULT_DRAFT_SKELETON_REPORT
    ensure_local_skeleton_fixture(skeleton_path)
    contract = build_generation_contract(draft_skeleton_path=skeleton_path)
    write_generation_contract(contract_path, contract)


def validate_generation_contract(contract_path: Path) -> list[str]:
    errors: list[str] = []
    if not contract_path.exists():
        return [f"generation contract not found: {contract_path}"]
    contract = read_json(contract_path)
    if contract.get("status") != "GENERATION_DISABLED_CONTRACT_READY":
        errors.append(f"contract status is not ready disabled: {contract.get('status')}")
    if contract.get("generation_adapter") != "disabled":
        errors.append(f"generation_adapter must be disabled: {contract.get('generation_adapter')}")
    if contract.get("draft_generation_enabled") is not False:
        errors.append("contract must keep draft_generation_enabled false")
    if contract.get("llm_call_allowed") is not False:
        errors.append("contract must keep llm_call_allowed false")
    if contract.get("llm_call_performed") is not False:
        errors.append("contract must keep llm_call_performed false")
    if int(contract.get("failed_count") or 0) != 0:
        errors.append(f"contract failed_count must be 0: {contract.get('failed_count')}")
    return errors


class DisabledVectorDraftGeneratorAdapter:
    adapter_name = "disabled"

    def generate(self, request: VectorDraftGenerationRequest) -> VectorDraftGenerationResult:
        root = repo_root()
        contract_path = Path(request.generation_contract_path)
        if not contract_path.is_absolute():
            contract_path = root / contract_path
        errors = validate_generation_contract(contract_path)
        reason = "DISABLED_ADAPTER_REFUSES_DRAFT_GENERATION"
        if errors:
            reason = "DISABLED_ADAPTER_INPUTS_INVALID"
        return VectorDraftGenerationResult(
            status="REFUSED",
            adapter_name=self.adapter_name,
            reason=reason,
            generation_contract_path=str(contract_path.relative_to(root)) if contract_path.is_relative_to(root) else str(contract_path),
            output_draft_path=DEFAULT_DRAFT_OUTPUT_REPORT,
            would_generate=False,
            draft_generation_enabled=False,
            llm_call_allowed=False,
            llm_call_performed=False,
            generated_text="",
            errors=errors,
        )


def get_vector_draft_generator_adapter(adapter_name: str) -> VectorDraftGeneratorAdapter:
    if adapter_name == "disabled":
        return DisabledVectorDraftGeneratorAdapter()
    raise ValueError(f"Unsupported vector draft generator adapter: {adapter_name}")


def build_disabled_generator_report(*, generation_contract_path: Path, adapter_name: str = "disabled") -> VectorDraftGenerationResult:
    ensure_generation_contract(generation_contract_path)
    root = repo_root()
    contract_relative = str(generation_contract_path.relative_to(root)) if generation_contract_path.is_relative_to(root) else str(generation_contract_path)
    adapter = get_vector_draft_generator_adapter(adapter_name)
    return adapter.generate(VectorDraftGenerationRequest(generation_contract_path=contract_relative, adapter_name=adapter_name))


def write_disabled_generator_report(path: Path, result: VectorDraftGenerationResult) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    root = repo_root()
    parser = argparse.ArgumentParser(description="Run disabled vector draft generator adapter.")
    parser.add_argument("--generation-contract", type=Path, default=root / DEFAULT_GENERATION_CONTRACT_REPORT)
    parser.add_argument("--adapter", default="disabled")
    parser.add_argument("--output", type=Path, default=root / DEFAULT_DISABLED_GENERATOR_REPORT)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = build_disabled_generator_report(generation_contract_path=args.generation_contract, adapter_name=args.adapter)
    write_disabled_generator_report(args.output, result)
    print(f"[gate18z:disabled-generator] Wrote disabled generator report: {args.output}")
    print(f"[gate18z:disabled-generator] status={result.status}")
    print(f"[gate18z:disabled-generator] reason={result.reason}")
    print("[gate18z:disabled-generator] draft_generation_enabled=false")
    print("[gate18z:disabled-generator] llm_call_performed=false")


if __name__ == "__main__":
    main()
