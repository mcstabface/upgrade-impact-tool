from __future__ import annotations

from app.scripts.actual_corpus_source_inventory_extraction import main as extract_inventory
from app.scripts.validate_actual_corpus_source_inventory_extraction import run_validation


def main() -> None:
    run_validation()
    extract_inventory()
    print("[gate21e] Pipeline complete")
    print("[gate21e] Actual corpus source inventory extraction completed for kbs/raw")


if __name__ == "__main__":
    main()
