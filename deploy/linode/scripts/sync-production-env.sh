#!/usr/bin/env bash
# Write production env files from environment variables (GitHub Actions secrets).
# Only updates keys that are set and non-empty — existing server values are preserved.
#
# Usage (on server):
#   export PRODUCTION_URL=https://jobs.nevil.ca
#   export CLIENT_ID=... CLIENT_SECRET=...   # or GITHUB_ID / GITHUB_SECRET
#   bash deploy/linode/scripts/sync-production-env.sh
#
# GitHub Actions cannot use secret names starting with GITHUB_ — use CLIENT_ID / CLIENT_SECRET.
# When OAuth credentials are present, auth is enabled automatically.
set -euo pipefail

APP_ROOT="${APP_ROOT:-/opt/jobpilot}"
BACKEND_ENV="$APP_ROOT/backend/.env"
FRONTEND_ENV="$APP_ROOT/frontend/.env.local"

# Map GitHub Actions names (CLIENT_*) to app env names (GITHUB_*)
if [[ -n "${CLIENT_ID:-}" ]]; then export GITHUB_ID="$CLIENT_ID"; fi
if [[ -n "${CLIENT_SECRET:-}" ]]; then export GITHUB_SECRET="$CLIENT_SECRET"; fi

set_env_var() {
  local file="$1" key="$2" value="$3"
  touch "$file"
  if grep -q "^${key}=" "$file" 2>/dev/null; then
    grep -v "^${key}=" "$file" > "${file}.tmp"
    mv "${file}.tmp" "$file"
  fi
  printf '%s=%s\n' "$key" "$value" >> "$file"
}

set_if_set() {
  local file="$1" key="$2"
  local val="${!key-}"
  if [[ -n "$val" ]]; then
    set_env_var "$file" "$key" "$val"
    echo "  updated $key in $(basename "$file")"
  fi
}

echo "==> Syncing production env (APP_ROOT=$APP_ROOT)"

# Derive URL-based settings from PRODUCTION_URL when provided
if [[ -n "${PRODUCTION_URL:-}" ]]; then
  set_env_var "$BACKEND_ENV" "ALLOWED_ORIGINS" "$PRODUCTION_URL"
  set_env_var "$FRONTEND_ENV" "NEXTAUTH_URL" "$PRODUCTION_URL"
  set_env_var "$FRONTEND_ENV" "NEXT_PUBLIC_API_URL" "$PRODUCTION_URL"
  echo "  updated ALLOWED_ORIGINS, NEXTAUTH_URL, NEXT_PUBLIC_API_URL from PRODUCTION_URL"
fi

# Backend
for key in \
  NEON_CONNECTION_STRING DATABASE_URL SECRET_KEY CRON_SECRET \
  DISABLE_APSCHEDULER JOB_INTELLIGENCE_ENABLED TARGET_PROVINCES \
  ADZUNA_APP_ID ADZUNA_APP_KEY RAPIDAPI_KEY JOB_BANK_API_KEY \
  SCRAPER_TIMEZONE SCRAPER_MORNING_HOUR SCRAPER_EVENING_HOUR \
  SCRAPER_FETCH_DESCRIPTIONS AUTH_DISABLED; do
  set_if_set "$BACKEND_ENV" "$key"
done

# Frontend OAuth + auth flags
for key in \
  NEXTAUTH_URL NEXTAUTH_SECRET NEXT_PUBLIC_API_URL \
  GITHUB_ID GITHUB_SECRET \
  AUTH_DISABLED NEXT_PUBLIC_AUTH_DISABLED NEXT_PUBLIC_HAS_GITHUB; do
  set_if_set "$FRONTEND_ENV" "$key"
done

# Mirror backend AUTH_DISABLED to frontend public flag when only backend key is synced
if [[ -n "${AUTH_DISABLED:-}" ]]; then
  set_env_var "$FRONTEND_ENV" "NEXT_PUBLIC_AUTH_DISABLED" "$AUTH_DISABLED"
fi

# Auto-enable GitHub auth when OAuth credentials are present
if [[ -n "${GITHUB_ID:-}" && -n "${GITHUB_SECRET:-}" ]]; then
  set_env_var "$BACKEND_ENV" "AUTH_DISABLED" "false"
  set_env_var "$FRONTEND_ENV" "AUTH_DISABLED" "false"
  set_env_var "$FRONTEND_ENV" "NEXT_PUBLIC_AUTH_DISABLED" "false"
  set_env_var "$FRONTEND_ENV" "NEXT_PUBLIC_HAS_GITHUB" "1"
  echo "  enabled GitHub OAuth (AUTH_DISABLED=false)"
elif [[ -n "${ENABLE_AUTH:-}" && "${ENABLE_AUTH}" == "true" ]]; then
  set_env_var "$BACKEND_ENV" "AUTH_DISABLED" "false"
  set_env_var "$FRONTEND_ENV" "AUTH_DISABLED" "false"
  set_env_var "$FRONTEND_ENV" "NEXT_PUBLIC_AUTH_DISABLED" "false"
  echo "  enabled auth (ENABLE_AUTH=true)"
fi

echo "==> Env sync complete"
