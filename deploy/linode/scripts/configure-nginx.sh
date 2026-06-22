#!/usr/bin/env bash
# Configure Nginx reverse proxy and obtain Let's Encrypt certificate.
# Usage:
#   sudo CERTBOT_EMAIL=you@example.com bash configure-nginx.sh your-subdomain.duckdns.org
#   sudo APP_DOMAIN=your-subdomain.duckdns.org CERTBOT_EMAIL=you@example.com bash configure-nginx.sh
set -euo pipefail

APP_DOMAIN="${1:-${APP_DOMAIN:-}}"
APP_ROOT="${APP_ROOT:-/opt/jobpilot}"
CERTBOT_EMAIL="${CERTBOT_EMAIL:-}"

if [[ -z "$APP_DOMAIN" ]]; then
  echo "Error: Pass domain as argument or set APP_DOMAIN." >&2
  echo "Example: sudo CERTBOT_EMAIL=you@example.com bash configure-nginx.sh your-subdomain.duckdns.org" >&2
  exit 1
fi

if [[ -z "$CERTBOT_EMAIL" ]]; then
  echo "Error: Set CERTBOT_EMAIL for Let's Encrypt (e.g. CERTBOT_EMAIL=you@example.com)." >&2
  exit 1
fi

TEMPLATE="$APP_ROOT/deploy/linode/nginx/jobpilot-http-domain.conf.template"
DEST="/etc/nginx/sites-available/jobpilot.conf"

sed "s|__APP_DOMAIN__|$APP_DOMAIN|g" "$TEMPLATE" > "$DEST"
ln -sf "$DEST" /etc/nginx/sites-enabled/jobpilot.conf
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl reload nginx

certbot --nginx -d "$APP_DOMAIN" --non-interactive --agree-tos -m "$CERTBOT_EMAIL" --redirect || {
  echo "Certbot failed. Ensure DNS points to this server and port 80 is open." >&2
  echo "If using Cloudflare proxy (orange cloud), set jobs to DNS-only (grey cloud) and retry." >&2
  exit 1
}

nginx -t
systemctl reload nginx

echo "Nginx configured for https://$APP_DOMAIN"
