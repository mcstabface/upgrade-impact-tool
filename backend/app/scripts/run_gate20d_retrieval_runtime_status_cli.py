from __future__ import annotations

from app.scripts.retrieval_runtime_status_cli import main as print_status
from app.scripts.validate_retrieval_runtime_status_cli import run_validation


def main() -> None:
    run_validation()
    print_status()
    print("[gate20d] Pipeline complete")
    print("[gate20d] Retrieval runtime status CLI exposes BM25-authoritative fail-closed posture")


if __name__ == "__main__":
    main()
