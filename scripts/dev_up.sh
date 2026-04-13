#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Starting backend..."
(
  cd "$ROOT_DIR/backend"
  python -m uvicorn app.main:app --reload --port 8000
) &

echo "Starting frontend..."
(
  cd "$ROOT_DIR/frontend"
  npm run dev
) &