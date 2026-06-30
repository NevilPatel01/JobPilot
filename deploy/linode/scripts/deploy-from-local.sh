#!/usr/bin/env bash
# Sync this checkout to a Linode server that does not have Git installed, then rebuild/restart.
set -euo pipefail

DEPLOY_HOST="${DEPLOY_HOST:-}"
DEPLOY_USER="${DEPLOY_USER:-root}"
APP_ROOT="${APP_ROOT:-/opt/jobpilot}"
SSH_OPTS="${SSH_OPTS:-}"

if [[ -z "$DEPLOY_HOST" ]]; then
  echo "Usage: DEPLOY_HOST=139.177.194.149 bash deploy/linode/scripts/deploy-from-local.sh" >&2
  exit 1
fi

echo "==> Syncing code to ${DEPLOY_USER}@${DEPLOY_HOST}:${APP_ROOT}"
rsync -az --delete \
  --exclude ".git" \
  --exclude "backend/.venv" \
  --exclude "backend/.env" \
  --exclude "frontend/node_modules" \
  --exclude "frontend/.env.local" \
  --exclude "frontend/.next" \
  --exclude "docs" \
  -e "ssh ${SSH_OPTS}" \
  ./ "${DEPLOY_USER}@${DEPLOY_HOST}:${APP_ROOT}/"

echo "==> Installing/rebuilding on server"
set +e
ssh ${SSH_OPTS} "${DEPLOY_USER}@${DEPLOY_HOST}" \
  "cd '${APP_ROOT}' && \
   if [[ ! -f backend/.env || ! -f frontend/.env.local ]]; then \
     echo 'Code upload complete. Create backend/.env and frontend/.env.local on the server, then rerun this script.'; \
     exit 42; \
   fi; \
   APP_ROOT='${APP_ROOT}' APP_USER='${DEPLOY_USER}' bash deploy/linode/scripts/install-app.sh"
install_status=$?
set -e

if [[ "$install_status" -eq 42 ]]; then
  exit 0
elif [[ "$install_status" -ne 0 ]]; then
  exit "$install_status"
fi

echo "==> Verifying API health"
ssh ${SSH_OPTS} "${DEPLOY_USER}@${DEPLOY_HOST}" \
  "bash '${APP_ROOT}/deploy/linode/scripts/wait-for-api-health.sh'"

echo "No-Git deploy complete."
