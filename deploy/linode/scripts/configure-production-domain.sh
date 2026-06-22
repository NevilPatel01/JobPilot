#!/usr/bin/env bash
# Point JobPilot at a production domain: env files, frontend rebuild, nginx + HTTPS.
# Usage: sudo CERTBOT_EMAIL=you@example.com bash configure-production-domain.sh your-subdomain.duckdns.org
set -euo pipefail

APP_DOMAIN="${1:-}"
APP_ROOT="${APP_ROOT:-/opt/jobpilot}"

if [[ -z "$APP_DOMAIN" ]]; then
  echo "Usage: sudo CERTBOT_EMAIL=you@example.com bash configure-production-domain.sh your-subdomain.duckdns.org" >&2
  exit 1
fi

BASE_URL="https://${APP_DOMAIN}"

echo "==> Updating backend .env"
BACKEND_ENV="$APP_ROOT/backend/.env"
grep -v '^ALLOWED_ORIGINS=' "$BACKEND_ENV" | grep -v '^AUTH_DISABLED=' > "${BACKEND_ENV}.tmp" || true
mv "${BACKEND_ENV}.tmp" "$BACKEND_ENV"
cat >> "$BACKEND_ENV" <<EOF
ALLOWED_ORIGINS=${BASE_URL}
AUTH_DISABLED=true
EOF

echo "==> Updating frontend .env.local"
cat > "$APP_ROOT/frontend/.env.local" <<EOF
NEXTAUTH_URL=${BASE_URL}
NEXTAUTH_SECRET=$(grep '^NEXTAUTH_SECRET=' "$APP_ROOT/frontend/.env.local" 2>/dev/null | cut -d= -f2- || openssl rand -hex 32)
GITHUB_ID=
GITHUB_SECRET=
NEXT_PUBLIC_API_URL=${BASE_URL}
AUTH_DISABLED=true
NEXT_PUBLIC_AUTH_DISABLED=true
NEXT_PUBLIC_HAS_GITHUB=
EOF

echo "==> Rebuilding frontend"
cd "$APP_ROOT/frontend"
npm run build
cp -r public .next/standalone/public
cp -r .next/static .next/standalone/.next/static

echo "==> Nginx + HTTPS"
bash "$APP_ROOT/deploy/linode/scripts/configure-nginx.sh" "$APP_DOMAIN"

systemctl restart jobpilot-api jobpilot-web
systemctl reload nginx

echo ""
echo "Done: ${BASE_URL}"
echo "API health: curl -sf ${BASE_URL}/api/v1/health"
echo "When GitHub OAuth is ready, set GITHUB_ID/SECRET in frontend/.env.local,"
echo "set AUTH_DISABLED=false in both env files, rebuild frontend, restart services."
