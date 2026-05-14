from __future__ import annotations

from app.scripts.actual_corpus_demo_readiness import main as report_actual_corpus
from app.scripts.validate_actual_corpus_demo_readiness import run_validation


def main() -> None:
    run_validation()
    report_actual_corpus()
    print("[gate21c] Pipeline complete")
    print("[gate21c] Actual corpus demo readiness assessment completed for kbs/raw")


if __name__ == "__main__":
    main()
