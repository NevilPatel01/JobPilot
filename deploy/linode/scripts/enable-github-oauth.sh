#!/usr/bin/env bash
# Enable GitHub OAuth on the production server.
# Usage: CLIENT_ID=... CLIENT_SECRET=... bash enable-github-oauth.sh
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/jobpilot}"
FRONTEND_ENV="$APP_ROOT/frontend/.env.local"
BACKEND_ENV="$APP_ROOT/backend/.env"

CLIENT_ID="${CLIENT_ID:-${GITHUB_ID:-}}"
CLIENT_SECRET="${CLIENT_SECRET:-${GITHUB_SECRET:-}}"

if [[ -z "$CLIENT_ID" || -z "$CLIENT_SECRET" ]]; then
  echo "Usage: CLIENT_ID=your_client_id CLIENT_SECRET=your_client_secret bash $0" >&2
  exit 1
fi

export CLIENT_ID CLIENT_SECRET
export GITHUB_ID="$CLIENT_ID" GITHUB_SECRET="$CLIENT_SECRET"
export PRODUCTION_URL="${PRODUCTION_URL:-$(grep '^NEXTAUTH_URL=' "$FRONTEND_ENV" | cut -d= -f2-)}"

bash "$APP_ROOT/deploy/linode/scripts/sync-production-env.sh"

echo "==> Rebuilding frontend"
cd "$APP_ROOT/frontend"
npm run build
cp -r public .next/standalone/public
cp -r .next/static .next/standalone/.next/static

systemctl restart jobpilot-api jobpilot-web
bash "$APP_ROOT/deploy/linode/scripts/wait-for-api-health.sh"

echo "GitHub OAuth enabled at ${PRODUCTION_URL}/login"
