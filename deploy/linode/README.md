# JobPilot — Linode deployment

Deploy JobPilot on a **single Linode VPS** with **Neon PostgreSQL** (no Docker).  
Secrets live only on the server and in **GitHub Actions repository secrets** — never in git.

## Security (public repo)

This directory is **safe to commit**. It contains only placeholders and automation scripts.

| Safe in git | Never commit |
|-------------|--------------|
| `env/*.example` templates | `backend/.env`, `frontend/.env.local` on the server |
| `nginx/*.template`, `jobpilot-http.conf` | Filled `deploy/linode/env/backend.env` or `frontend.env.local` |
| `scripts/*.sh`, `systemd/*.service` | TLS private keys, Neon passwords, OAuth secrets, `CRON_SECRET` values |
| | GitHub OAuth client secret, API keys (Adzuna, RapidAPI, etc.) |

On the server, copy examples then edit locally:

```bash
cp deploy/linode/env/backend.env.example backend/.env
cp deploy/linode/env/frontend.env.local.example frontend/.env.local
```

Generate secrets on the server: `openssl rand -hex 32`

## Before you start

| Item | Your value | Notes |
|------|------------|--------|
| Linode public IP | `YOUR_LINODE_IP` | Firewall: allow **22, 80, 443** |
| HTTPS hostname | `your-subdomain.duckdns.org` | [DuckDNS](https://www.duckdns.org) free — required for GitHub OAuth |
| Neon DB | `NEON_CONNECTION_STRING` in `backend/.env` | Or `DATABASE_URL` with `postgresql+asyncpg://` |
| GitHub OAuth App | Client ID + Secret | Callback: `https://YOUR_HOST/api/auth/callback/github` |
| `CRON_SECRET` | Random string | For GitHub Actions scraper cron |
| `SECRET_KEY` / `NEXTAUTH_SECRET` | Random strings | `openssl rand -hex 32` |
| `CERTBOT_EMAIL` | Your email | Let's Encrypt registration (not stored in repo) |

**GitHub OAuth app:** [Developer settings → OAuth Apps](https://github.com/settings/developers)

- Homepage URL: `https://YOUR_HOST`
- Callback URL: `https://YOUR_HOST/api/auth/callback/github`

## Architecture

```text
Internet → DuckDNS → Linode (Nginx :443)
                         ├── /api/auth/*  → Next.js :3000 (NextAuth)
                         ├── /api/v1/*    → FastAPI :8000
                         ├── /socket.io/* → FastAPI :8000
                         └── /*           → Next.js :3000
                    Neon Postgres (external)
                    GitHub Actions → POST /api/v1/internal/cron/scrape
```

## Quick deploy (on the Linode)

SSH as root (or sudo user), then:

```bash
# 1. Bootstrap OS packages (Python, Node, Nginx, Certbot)
sudo bash deploy/linode/scripts/bootstrap-server.sh

# 2. Clone repo (replace with your fork URL)
sudo mkdir -p /opt/jobpilot
sudo chown "$USER":"$USER" /opt/jobpilot
git clone https://github.com/YOUR_USER/JobPilot.git /opt/jobpilot
cd /opt/jobpilot

# 3. Create env files from templates (edit with real secrets on server only)
cp deploy/linode/env/backend.env.example backend/.env
cp deploy/linode/env/frontend.env.local.example frontend/.env.local
nano backend/.env
nano frontend/.env.local

# 4. Install app + systemd services
sudo bash deploy/linode/scripts/install-app.sh

# 5. Optional: HTTP-only via IP before DNS is ready
sudo bash deploy/linode/scripts/configure-http-nginx.sh

# 6. Configure Nginx + HTTPS (domain + certbot email required)
sudo CERTBOT_EMAIL=you@example.com bash deploy/linode/scripts/configure-nginx.sh your-subdomain.duckdns.org

# 7. Check status
sudo systemctl status jobpilot-api jobpilot-web nginx
curl -s https://your-subdomain.duckdns.org/api/v1/health
```

### Staged domain setup (auth disabled until OAuth is ready)

```bash
sudo CERTBOT_EMAIL=you@example.com bash deploy/linode/scripts/configure-production-domain.sh your-subdomain.duckdns.org
```

This sets `AUTH_DISABLED=true`, configures HTTPS, and prints steps to enable GitHub OAuth when ready.

## Environment files (on server only)

### `backend/.env`

| Variable | Example |
|----------|---------|
| `NEON_CONNECTION_STRING` | From Neon dashboard (`postgresql://...?sslmode=require`) |
| `SECRET_KEY` | `openssl rand -hex 32` |
| `ALLOWED_ORIGINS` | `https://your-subdomain.duckdns.org` |
| `AUTH_DISABLED` | `false` |
| `CRON_SECRET` | `openssl rand -hex 32` |
| `DISABLE_APSCHEDULER` | `false` (or `true` if only GitHub Actions runs scrapers) |

### `frontend/.env.local`

| Variable | Example |
|----------|---------|
| `NEXTAUTH_URL` | `https://your-subdomain.duckdns.org` |
| `NEXTAUTH_SECRET` | `openssl rand -hex 32` |
| `NEXT_PUBLIC_API_URL` | `https://your-subdomain.duckdns.org` |
| `GITHUB_ID` / `GITHUB_SECRET` | From OAuth app |
| `AUTH_DISABLED` | `false` |
| `NEXT_PUBLIC_AUTH_DISABLED` | `false` |

Rebuild frontend after env changes:

```bash
cd /opt/jobpilot/frontend && npm run build
cp -r public .next/standalone/public
cp -r .next/static .next/standalone/.next/static
sudo systemctl restart jobpilot-web
```

## GitHub Actions cron

Add repository **Secrets** (Settings → Secrets and variables → Actions):

| Secret | Value |
|--------|--------|
| `CRON_SECRET` | Same as backend `.env` |
| `PRODUCTION_URL` | `https://your-subdomain.duckdns.org` |

Add a repository **Variable** (Settings → Secrets and variables → Actions → Variables):

| Variable | Value |
|----------|--------|
| `ENABLE_PRODUCTION_SCRAPE` | `true` |

Workflow: `.github/workflows/scrape.yml` (runs 08:00 and 18:00 America/Toronto when enabled).

The cron endpoint returns **404** when `CRON_SECRET` is unset, so local/dev installs are not exposed.

## Updates

```bash
cd /opt/jobpilot
sudo bash deploy/linode/scripts/deploy.sh
```

The deploy script pulls the latest code, installs backend dependencies, applies pending Alembic migrations, rebuilds the frontend, and restarts both services.

## Firewall (Linode Cloud Firewall)

| Direction | Protocol | Port | Source |
|-----------|----------|------|--------|
| Inbound | TCP | 22 | Your IP (recommended) |
| Inbound | TCP | 80 | 0.0.0.0/0 |
| Inbound | TCP | 443 | 0.0.0.0/0 |
| Outbound | All | All | 0.0.0.0/0 (Neon, APIs, apt) |

Do **not** expose ports 3000 or 8000 publicly — Nginx proxies locally.

## Troubleshooting

| Issue | Check |
|-------|--------|
| OAuth redirect error | `NEXTAUTH_URL` and GitHub callback URL must match exactly |
| API CORS errors | `ALLOWED_ORIGINS` includes your HTTPS host |
| DB connection failed | Neon IP allowlist (allow all `0.0.0.0/0` for Linode) or disable IP restrict |
| PDF fails | `which tectonic` on server; re-run `scripts/ensure-tectonic.sh` |
| URL import fails | `playwright install chromium` + `playwright install-deps` |
| Scraper cron 401 | `CRON_SECRET` matches in `.env` and GitHub Secrets |
| Scraper cron skipped | Set `ENABLE_PRODUCTION_SCRAPE=true` repository variable |

Logs:

```bash
sudo journalctl -u jobpilot-api -f
sudo journalctl -u jobpilot-web -f
```

## Files in this directory

| Path | Purpose |
|------|---------|
| `env/backend.env.example` | Backend template (placeholders only) |
| `env/frontend.env.local.example` | Frontend template (placeholders only) |
| `env/.gitignore` | Blocks accidental commit of filled env files |
| `scripts/bootstrap-server.sh` | OS dependencies (Python, Node, Nginx, Certbot) |
| `scripts/install-app.sh` | venv, npm build, systemd enable |
| `scripts/configure-http-nginx.sh` | HTTP reverse proxy via IP (pre-HTTPS) |
| `scripts/configure-nginx.sh` | Domain Nginx + Let's Encrypt HTTPS |
| `scripts/configure-production-domain.sh` | Domain + env + rebuild (auth off until OAuth) |
| `scripts/deploy.sh` | `git pull` + rebuild + restart |
| `systemd/jobpilot-api.service` | FastAPI on `127.0.0.1:8000` |
| `systemd/jobpilot-web.service` | Next.js standalone on `127.0.0.1:3000` |
| `nginx/jobpilot-http.conf` | HTTP default server (IP access, no domain) |
| `nginx/jobpilot-http-domain.conf.template` | HTTP bootstrap for certbot (`__APP_DOMAIN__`) |
| `nginx/jobpilot.conf.template` | Full HTTPS reference template (`__APP_DOMAIN__`) |
