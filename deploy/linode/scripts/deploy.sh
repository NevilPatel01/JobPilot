#!/usr/bin/env bash
# Pull latest code, rebuild, and restart services.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/jobpilot}"

cd "$APP_ROOT"
if [[ -d "$APP_ROOT/.git" ]]; then
  git pull --ff-only
else
  echo "No git repo at APP_ROOT — skipping git pull (use GitHub Actions rsync deploy)."
fi

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
for i in 1 2 3 4 5 6 7 8 9 10; do
  if curl -sf "http://127.0.0.1:8000/api/v1/health" >/dev/null; then
    echo " API healthy"
    exit 0
  fi
  sleep 2
done
echo "Warning: API health check timed out" >&2
exit 1
