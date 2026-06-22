#!/usr/bin/env bash
# Start PostgreSQL, backend, and frontend for local development.
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PIDS=()

cleanup() {
  echo ""
  echo "Shutting down..."
  if ((${#PIDS[@]} > 0)); then
    for pid in "${PIDS[@]}"; do
      kill "$pid" 2>/dev/null || true
    done
  fi
  wait 2>/dev/null || true
}
trap cleanup EXIT INT TERM

require_cmd() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Error: '$1' is required but not installed." >&2
    exit 1
  fi
}

require_cmd docker
require_cmd python3
require_cmd bun

if ! docker compose version >/dev/null 2>&1; then
  echo "Error: 'docker compose' is required but not available." >&2
  exit 1
fi

# --- PostgreSQL (Docker) ---
echo "Starting PostgreSQL..."
docker compose up postgres -d --wait

# --- Env files ---
if [ ! -f "$ROOT_DIR/backend/.env" ]; then
  echo "Creating backend/.env from .env.example"
  cp "$ROOT_DIR/backend/.env.example" "$ROOT_DIR/backend/.env"
fi

if [ ! -f "$ROOT_DIR/frontend/.env.local" ]; then
  echo "Creating frontend/.env.local from .env.local.example"
  cp "$ROOT_DIR/frontend/.env.local.example" "$ROOT_DIR/frontend/.env.local"
fi

# --- Backend setup ---
if [ ! -d "$ROOT_DIR/backend/.venv" ]; then
  echo "Creating backend virtual environment..."
  python3 -m venv "$ROOT_DIR/backend/.venv"
  "$ROOT_DIR/backend/.venv/bin/pip" install -r "$ROOT_DIR/backend/requirements.txt"
fi

# --- Frontend setup ---
if [ ! -d "$ROOT_DIR/frontend/node_modules" ]; then
  echo "Installing frontend dependencies..."
  bun install --prefix "$ROOT_DIR/frontend"
fi

# Backend/frontend run on the host; Postgres is in Docker on localhost:5432.
# Always use localhost here — backend/.env.example uses the Docker service name
# "postgres", which only resolves inside the compose network, not on your Mac.
export DATABASE_URL="postgresql+asyncpg://jobpilot:password@localhost:5432/jobpilot"
export AUTH_DISABLED="true"
export ALLOWED_ORIGINS="http://localhost:3000"

echo ""
echo "Starting backend  → http://localhost:8000"
echo "Starting frontend → http://localhost:3000"
echo "PostgreSQL        → localhost:5432"
echo ""
echo "Press Ctrl+C to stop all services."
echo ""

(
  cd "$ROOT_DIR/backend"
  source .venv/bin/activate
  exec uvicorn app.main:socket_app --reload --host 0.0.0.0 --port 8000
) &
PIDS+=($!)

(
  cd "$ROOT_DIR/frontend"
  exec bun run dev
) &
PIDS+=($!)

wait
