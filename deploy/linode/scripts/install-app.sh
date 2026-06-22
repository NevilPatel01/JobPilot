#!/usr/bin/env bash
# Install JobPilot into /opt/jobpilot and enable systemd services.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/jobpilot}"
APP_USER="${APP_USER:-${SUDO_USER:-$USER}}"

if [[ ! -d "$APP_ROOT/backend" || ! -d "$APP_ROOT/frontend" ]]; then
  echo "Error: $APP_ROOT must contain backend/ and frontend/. Clone the repo first." >&2
  exit 1
fi

if [[ ! -f "$APP_ROOT/backend/.env" ]]; then
  echo "Error: Create $APP_ROOT/backend/.env from deploy/linode/env/backend.env.example" >&2
  exit 1
fi

if [[ ! -f "$APP_ROOT/frontend/.env.local" ]]; then
  echo "Error: Create $APP_ROOT/frontend/.env.local from deploy/linode/env/frontend.env.local.example" >&2
  exit 1
fi

echo "==> Python backend"
cd "$APP_ROOT/backend"
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
playwright install chromium
playwright install-deps chromium || true
bash "$APP_ROOT/scripts/ensure-tectonic.sh"
deactivate

echo "==> Frontend build"
cd "$APP_ROOT/frontend"
npm ci
npm run build
cp -r public .next/standalone/public
cp -r .next/static .next/standalone/.next/static

echo "==> systemd units"
install -m 0644 "$APP_ROOT/deploy/linode/systemd/jobpilot-api.service" /etc/systemd/system/
install -m 0644 "$APP_ROOT/deploy/linode/systemd/jobpilot-web.service" /etc/systemd/system/

sed -i "s|__APP_ROOT__|$APP_ROOT|g" /etc/systemd/system/jobpilot-api.service
sed -i "s|__APP_USER__|$APP_USER|g" /etc/systemd/system/jobpilot-api.service
sed -i "s|__APP_ROOT__|$APP_ROOT|g" /etc/systemd/system/jobpilot-web.service
sed -i "s|__APP_USER__|$APP_USER|g" /etc/systemd/system/jobpilot-web.service

systemctl daemon-reload
systemctl enable jobpilot-api jobpilot-web
systemctl restart jobpilot-api jobpilot-web

echo "Install complete."
systemctl --no-pager status jobpilot-api jobpilot-web || true
