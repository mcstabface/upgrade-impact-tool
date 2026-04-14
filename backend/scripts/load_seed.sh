#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -z "${DATABASE_URL:-}" ]]; then
  export DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:5432/upgrade_impact_tool"
fi

psql "$DATABASE_URL" -f "$ROOT_DIR/seeds/seed_001.sql"

psql "$DATABASE_URL" -c "
SELECT setval(pg_get_serial_sequence('customers', 'customer_id'), COALESCE((SELECT MAX(customer_id) FROM customers), 1), true);
SELECT setval(pg_get_serial_sequence('environments', 'environment_id'), COALESCE((SELECT MAX(environment_id) FROM environments), 1), true);
SELECT setval(pg_get_serial_sequence('customer_state_snapshots', 'snapshot_id'), COALESCE((SELECT MAX(snapshot_id) FROM customer_state_snapshots), 1), true);
SELECT setval(pg_get_serial_sequence('customer_applications', 'customer_application_id'), COALESCE((SELECT MAX(customer_application_id) FROM customer_applications), 1), true);
SELECT setval(pg_get_serial_sequence('customer_modules', 'customer_module_id'), COALESCE((SELECT MAX(customer_module_id) FROM customer_modules), 1), true);
SELECT setval(pg_get_serial_sequence('kb_articles', 'kb_article_id'), COALESCE((SELECT MAX(kb_article_id) FROM kb_articles), 1), true);
SELECT setval(pg_get_serial_sequence('kb_article_versions', 'kb_article_version_id'), COALESCE((SELECT MAX(kb_article_version_id) FROM kb_article_versions), 1), true);
SELECT setval(pg_get_serial_sequence('change_records', 'change_id'), COALESCE((SELECT MAX(change_id) FROM change_records), 1), true);
SELECT setval(pg_get_serial_sequence('analysis_applications', 'analysis_application_id'), COALESCE((SELECT MAX(analysis_application_id) FROM analysis_applications), 1), true);
SELECT setval(pg_get_serial_sequence('analysis_findings', 'finding_id'), COALESCE((SELECT MAX(finding_id) FROM analysis_findings), 1), true);
SELECT setval(pg_get_serial_sequence('finding_evidence', 'finding_evidence_id'), COALESCE((SELECT MAX(finding_evidence_id) FROM finding_evidence), 1), true);
SELECT setval(pg_get_serial_sequence('state_transitions', 'state_transition_id'), COALESCE((SELECT MAX(state_transition_id) FROM state_transitions), 1), true);
"