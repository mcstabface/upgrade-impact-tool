#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

if [[ -z "${DATABASE_URL:-}" ]]; then
  export DATABASE_URL="postgresql://postgres:postgres@127.0.0.1:5432/upgrade_impact_tool"
fi

psql "$DATABASE_URL" -f "$ROOT_DIR/seeds/seed_001.sql"