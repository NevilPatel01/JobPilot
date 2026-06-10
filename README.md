# JobPilot

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](docker-compose.yml)
[![Next.js](https://img.shields.io/badge/Next.js-14-black?logo=next.js)](frontend/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi)](backend/)

A free, open-source job search command centre for tech professionals. JobPilot autonomously aggregates remote job listings, provides a Kanban application tracker, resume match scoring, and analytics — all in one dashboard.

> **Paste a job URL, we do the rest.** The URL importer is JobPilot's killer feature — no manual form filling required.

## Features

| Feature | Description |
|---------|-------------|
| Job Scraper | RemoteOK, WeWorkRemotely, and Hacker News with smart deduplication |
| Kanban Tracker | Drag-and-drop: To Apply → Applied → Interviewing → Offer → Rejected |
| URL Importer | Paste any careers page URL to auto-fill job details (Playwright) |
| Resume Match | TF-IDF keyword matching with visible matched keywords |
| Analytics | Application trends, interview rate, status breakdown (Chart.js) |
| Dark UI | Premium zinc/indigo dashboard inspired by Linear and Supabase |

## Architecture

```
┌─────────────┐     REST API      ┌─────────────┐     SQL      ┌────────────┐
│  Next.js 14 │ ◄──────────────► │   FastAPI   │ ◄──────────► │ PostgreSQL │
│  Frontend   │   /api/v1/*      │   Backend   │              │     15     │
└─────────────┘                   └─────────────┘              └────────────┘
                                        │
                                  APScheduler
                                  Daily 02:00 UTC
                                  (job scrapers)
```

## Quick Start (Docker)

```bash
git clone https://github.com/NevilPatel01/JobPilot.git
cd JobPilot
cp backend/.env.example backend/.env
cp frontend/.env.local.example frontend/.env.local
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000/api/v1/health |
| PostgreSQL | localhost:5432 |

Dev mode runs with `AUTH_DISABLED=true` — no OAuth setup required for local testing.

## Local Development (without Docker)

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Start PostgreSQL locally and update DATABASE_URL in .env
uvicorn app.main:socket_app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
npm run dev
```

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `DATABASE_URL` | PostgreSQL connection string (asyncpg) |
| `SECRET_KEY` | JWT signing key — generate a random 256-bit value |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins |
| `GOOGLE_CLIENT_ID` | Google OAuth client ID (optional) |
| `GITHUB_CLIENT_ID` | GitHub OAuth client ID (optional) |
| `AUTH_DISABLED` | Set `true` for local dev without OAuth |
| `SCRAPER_DEBOUNCE_MINUTES` | Min minutes between manual scrapes (default: 10) |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXTAUTH_URL` | App URL (e.g. `http://localhost:3000`) |
| `NEXTAUTH_SECRET` | NextAuth secret — generate a random value |
| `NEXT_PUBLIC_API_URL` | Backend URL (e.g. `http://localhost:8000`) |
| `GOOGLE_CLIENT_ID` / `GOOGLE_CLIENT_SECRET` | Google OAuth (optional) |
| `GITHUB_ID` / `GITHUB_SECRET` | GitHub OAuth (optional) |
| `AUTH_DISABLED` / `NEXT_PUBLIC_AUTH_DISABLED` | Skip OAuth in dev |

Never commit `.env` or `.env.local` files. Use the `.example` files as templates.

## Deployment

JobPilot can be deployed to Railway, Render, or Fly.io:

1. Provision a PostgreSQL database
2. Deploy the backend with environment variables from the table above
3. Deploy the frontend with `NEXT_PUBLIC_API_URL` pointing to your backend
4. Set `AUTH_DISABLED=false` and configure OAuth providers for production

For self-hosting, use `docker compose up` on any VPS with Docker installed.

## Roadmap

See [ROADMAP.md](ROADMAP.md) — community forums, real-time chat, job expiry checker, and push notifications are planned for v0.2+.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). The most impactful contribution is adding a new job scraper source.

## License

[MIT](LICENSE) — free forever.
