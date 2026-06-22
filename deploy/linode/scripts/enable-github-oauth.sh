#!/usr/bin/env bash
# Enable GitHub OAuth on the production server.
# Usage: GITHUB_ID=... GITHUB_SECRET=... bash enable-github-oauth.sh
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/jobpilot}"
FRONTEND_ENV="$APP_ROOT/frontend/.env.local"
BACKEND_ENV="$APP_ROOT/backend/.env"

if [[ -z "${GITHUB_ID:-}" || -z "${GITHUB_SECRET:-}" ]]; then
  echo "Usage: GITHUB_ID=your_client_id GITHUB_SECRET=your_client_secret bash $0" >&2
  exit 1
fi

export GITHUB_ID GITHUB_SECRET
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
