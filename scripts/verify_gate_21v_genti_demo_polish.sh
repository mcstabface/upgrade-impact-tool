#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "${TMP_DIR}"' EXIT

DB_PATH="${TMP_DIR}/genti_review_workflow_demo.db"
REPORT_DIR="${TMP_DIR}/reports"
QUIET_OUT="${TMP_DIR}/quiet.out"
SHOW_FILES_OUT="${TMP_DIR}/show-files.out"

bash "${ROOT_DIR}/scripts/genti_demo.sh" quiet "${DB_PATH}" "${REPORT_DIR}" > "${QUIET_OUT}"
bash "${ROOT_DIR}/scripts/genti_demo.sh" show-files "${DB_PATH}" "${REPORT_DIR}" > "${SHOW_FILES_OUT}"

python3 - "${QUIET_OUT}" "${SHOW_FILES_OUT}" "${DB_PATH}" "${REPORT_DIR}" <<'PY'
from pathlib import Path
import sys

quiet_path = Path(sys.argv[1])
show_files_path = Path(sys.argv[2])
db_path = Path(sys.argv[3])
report_dir = Path(sys.argv[4])
quiet_text = quiet_path.read_text(encoding="utf-8")
show_files_text = show_files_path.read_text(encoding="utf-8")

failures = []
def require(condition, message):
    if not condition:
        failures.append(message)

require("Genti demo summary" in quiet_text, "quiet summary title missing")
require("bug_entries: 11" in quiet_text, "quiet bug count missing")
require("mismatch_flags: 11" in quiet_text, "quiet mismatch count missing")
require("report_files_present: 5" in quiet_text, "quiet report file count missing")
require("Gate 21R query/view validation passed" not in quiet_text, "quiet output is too noisy")
require("Gate 21S report/export validation passed" not in quiet_text, "quiet output includes report verifier noise")
require(db_path.exists(), "quiet command did not create demo DB")
require((report_dir / "genti_mismatch_review.csv").exists(), "quiet command did not create mismatch report")
require((report_dir / "genti_bug_136_detail.json").exists(), "quiet command did not create bug detail report")
require(str(db_path) in show_files_text, "show-files output missing DB path")
for name in [
    "genti_mismatch_review.csv",
    "genti_test_required.csv",
    "genti_bug_136_detail.json",
    "genti_audit_history.csv",
    "genti_mismatch_review.md",
]:
    require(str(report_dir / name) in show_files_text, f"show-files output missing {name}")

if failures:
    raise SystemExit("Gate 21V demo polish validation failed:\n- " + "\n- ".join(failures))

print("Gate 21V demo polish validation passed")
print("quiet_summary_present: 1")
print("quiet_noise_suppressed: 1")
print("show_files_paths_present: 6")
print("generated_reports_present: 5")
PY

# Validate the default-path clean command without touching the temp custom paths.
bash "${ROOT_DIR}/scripts/genti_demo.sh" prepare >/dev/null
if [[ ! -f "${ROOT_DIR}/artifacts/genti_review_workflow/genti_review_workflow_demo.db" ]]; then
  echo "default demo DB was not created before clean" >&2
  exit 1
fi
bash "${ROOT_DIR}/scripts/genti_demo.sh" clean >/dev/null
if [[ -e "${ROOT_DIR}/artifacts/genti_review_workflow" ]]; then
  echo "clean command did not remove default artifact directory" >&2
  exit 1
fi

echo "clean_removed_default_artifacts: 1"
