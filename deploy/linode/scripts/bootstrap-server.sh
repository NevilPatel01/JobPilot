#!/usr/bin/env bash
# Install OS packages for JobPilot on Ubuntu 22.04/24.04 (run on Linode with sudo).
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

apt-get update
apt-get install -y --no-install-recommends \
  ca-certificates \
  curl \
  git \
  nginx \
  python3 \
  python3-venv \
  python3-pip \
  certbot \
  python3-certbot-nginx \
  fontconfig \
  libnss3 \
  libatk-bridge2.0-0t64 \
  libdrm2 \
  libxkbcommon0 \
  libgbm1 \
  libasound2t64 \
  libxshmfence1

if ! command -v node >/dev/null 2>&1 || [[ "$(node -v)" != v20* ]]; then
  curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
  apt-get install -y nodejs
fi

echo "Bootstrap complete."
echo "Node: $(node -v)  Python: $(python3 --version)"
echo "Next: clone repo to /opt/jobpilot and run install-app.sh"
