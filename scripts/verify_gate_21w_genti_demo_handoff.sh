#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
HANDOFF="${ROOT_DIR}/docs/runbooks/Genti Review Workflow Demo Handoff Summary.md"

if [[ ! -f "${HANDOFF}" ]]; then
  echo "Missing handoff summary: ${HANDOFF}" >&2
  exit 1
fi

python3 - "${HANDOFF}" <<'PY'
from pathlib import Path
import sys

handoff = Path(sys.argv[1])
text = handoff.read_text(encoding="utf-8")
required_terms = [
    "Gate 21W — Genti Review Workflow Demo Handoff Summary",
    "Gate 21L",
    "Gate 21M",
    "Gate 21N",
    "Gate 21O",
    "Gate 21P",
    "Gate 21Q",
    "Gate 21R",
    "Gate 21S",
    "Gate 21T",
    "Gate 21U",
    "Gate 21V",
    "bash scripts/genti_demo.sh quiet",
    "bash scripts/genti_demo.sh all",
    "bash scripts/genti_demo.sh show-files",
    "bash scripts/genti_demo.sh clean",
    "bash scripts/verify_gate_21v_genti_demo_polish.sh",
    "bug_entries: 11",
    "mismatch_flags: 11",
    "test_required_entries: 1",
    "bug_pdf_artifacts: 3",
    "audit_events: 6",
    "report_files_present: 5",
    "artifacts/genti_review_workflow/genti_review_workflow_demo.db",
    "artifacts/genti_review_workflow/reports/genti_mismatch_review.csv",
    "artifacts/genti_review_workflow/reports/genti_test_required.csv",
    "artifacts/genti_review_workflow/reports/genti_bug_136_detail.json",
    "artifacts/genti_review_workflow/reports/genti_audit_history.csv",
    "artifacts/genti_review_workflow/reports/genti_mismatch_review.md",
    "Open Decisions for Genti",
    "Gate 21X — Genti Review Workflow APEX Implementation Decision Record",
]
missing = [term for term in required_terms if term not in text]
if missing:
    raise SystemExit("Gate 21W handoff validation failed:\n- missing: " + "\n- missing: ".join(missing))
print("Gate 21W demo handoff validation passed")
print(f"required_terms: {len(required_terms)}")
print("completed_gate_refs: 11")
print("demo_artifact_refs: 6")
PY
