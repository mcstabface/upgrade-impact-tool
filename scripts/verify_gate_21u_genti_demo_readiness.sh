#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PACKET="${ROOT_DIR}/docs/runbooks/Genti Review Workflow Demo Readiness Packet.md"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

if [[ ! -f "${PACKET}" ]]; then
  echo "Missing readiness packet: ${PACKET}" >&2
  exit 1
fi

python3 - "${PACKET}" <<'PY'
from pathlib import Path
import sys

packet = Path(sys.argv[1])
text = packet.read_text(encoding="utf-8")

required_terms = [
    "Gate 21U — Genti Review Workflow Demo Readiness Packet",
    "bash scripts/genti_demo.sh all",
    "bash scripts/genti_demo.sh prepare",
    "bash scripts/genti_demo.sh query",
    "bash scripts/genti_demo.sh reports",
    "bash scripts/genti_demo.sh summary",
    "bash scripts/verify_gate_21t_genti_demo_cli.sh",
    "artifacts/genti_review_workflow/genti_review_workflow_demo.db",
    "artifacts/genti_review_workflow/reports/genti_mismatch_review.csv",
    "artifacts/genti_review_workflow/reports/genti_test_required.csv",
    "artifacts/genti_review_workflow/reports/genti_bug_136_detail.json",
    "artifacts/genti_review_workflow/reports/genti_audit_history.csv",
    "artifacts/genti_review_workflow/reports/genti_mismatch_review.md",
    "rm -rf artifacts/genti_review_workflow/",
    "Generated files under `artifacts/genti_review_workflow/` are runtime artifacts.",
]

failures = [term for term in required_terms if term not in text]
if failures:
    raise SystemExit("Gate 21U readiness packet validation failed:\n- missing: " + "\n- missing: ".join(failures))

print("Gate 21U readiness packet content validation passed")
print(f"required_terms: {len(required_terms)}")
PY

bash "${ROOT_DIR}/scripts/verify_gate_21t_genti_demo_cli.sh" "${TMP_DIR}/genti_review_workflow_demo.db" "${TMP_DIR}/reports" >/dev/null

python3 - "${TMP_DIR}" <<'PY'
from pathlib import Path
import sys

tmp = Path(sys.argv[1])
expected = [
    tmp / "genti_review_workflow_demo.db",
    tmp / "reports" / "genti_mismatch_review.csv",
    tmp / "reports" / "genti_test_required.csv",
    tmp / "reports" / "genti_bug_136_detail.json",
    tmp / "reports" / "genti_audit_history.csv",
    tmp / "reports" / "genti_mismatch_review.md",
]
missing = [str(path) for path in expected if not path.exists() or path.stat().st_size == 0]
if missing:
    raise SystemExit("Gate 21U generated artifact validation failed:\n- missing/empty: " + "\n- missing/empty: ".join(missing))

print("Gate 21U demo readiness validation passed")
print("demo_db_present: 1")
print("report_files_present: 5")
PY
