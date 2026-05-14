from __future__ import annotations

from app.scripts.actual_corpus_search_context_summary import main as summarize_search_context
from app.scripts.validate_actual_corpus_search_context_summary import run_validation


def main() -> None:
    run_validation()
    summarize_search_context()
    print("[gate21i] Pipeline complete")
    print("[gate21i] Actual corpus search-context summary completed")


if __name__ == "__main__":
    main()
