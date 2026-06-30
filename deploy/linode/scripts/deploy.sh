#!/usr/bin/env bash
# Rebuild and restart services after code has been uploaded by CI/CD or rsync.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/jobpilot}"

cd "$APP_ROOT"
echo "Using uploaded code at $APP_ROOT. Git is not required on the server."

cd "$APP_ROOT/backend"
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
deactivate

bash "$APP_ROOT/scripts/ensure-tectonic.sh"

cd "$APP_ROOT/frontend"
npm ci
npm run build
cp -r public .next/standalone/public
cp -r .next/static .next/standalone/.next/static

systemctl restart jobpilot-api jobpilot-web

echo "Deploy complete."
bash "$APP_ROOT/deploy/linode/scripts/wait-for-api-health.sh"
