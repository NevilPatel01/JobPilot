#!/usr/bin/env bash
# Install HTTP-only Nginx config (IP access before DuckDNS/HTTPS).
set -euo pipefail
APP_ROOT="${APP_ROOT:-/opt/jobpilot}"
install -m 0644 "$APP_ROOT/deploy/linode/nginx/jobpilot-http.conf" /etc/nginx/sites-available/jobpilot.conf
ln -sf /etc/nginx/sites-available/jobpilot.conf /etc/nginx/sites-enabled/jobpilot.conf
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx
echo "HTTP proxy active on port 80"
