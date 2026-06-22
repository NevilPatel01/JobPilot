#!/usr/bin/env bash
# Wait for the local FastAPI health endpoint after a service restart.
set -euo pipefail

URL="${1:-http://127.0.0.1:8000/api/v1/health}"
ATTEMPTS="${WAIT_HEALTH_ATTEMPTS:-20}"
SLEEP_SECS="${WAIT_HEALTH_SLEEP:-2}"

for ((i = 1; i <= ATTEMPTS; i++)); do
  if curl -sf "$URL" >/dev/null; then
    curl -sf "$URL"
    echo ""
    echo "API healthy"
    exit 0
  fi
  sleep "$SLEEP_SECS"
done

echo "Warning: API health check timed out after $((ATTEMPTS * SLEEP_SECS))s" >&2
exit 1
