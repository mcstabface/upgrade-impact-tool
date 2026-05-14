from __future__ import annotations

from app.scripts.actual_corpus_search_context_extraction import main as extract_search_context
from app.scripts.validate_actual_corpus_search_context_extraction import run_validation


def main() -> None:
    run_validation()
    extract_search_context()
    print("[gate21h] Pipeline complete")
    print("[gate21h] Actual corpus search-context extraction completed")


if __name__ == "__main__":
    main()
