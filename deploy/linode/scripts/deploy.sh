#!/usr/bin/env bash
# Pull latest code, rebuild, and restart services.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/jobpilot}"

cd "$APP_ROOT"
git pull --ff-only

cd "$APP_ROOT/backend"
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
deactivate

cd "$APP_ROOT/frontend"
npm ci
npm run build
cp -r public .next/standalone/public
cp -r .next/static .next/standalone/.next/static

systemctl restart jobpilot-api jobpilot-web

echo "Deploy complete."
curl -sf "http://127.0.0.1:8000/api/v1/health" && echo " API healthy"
