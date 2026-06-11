# JobPilot — GitHub Copilot Instructions

JobPilot is a free, open-source job search platform: FastAPI backend + Next.js 14 frontend + PostgreSQL.

## Architecture

- `backend/` — FastAPI, SQLAlchemy 2.0, async PostgreSQL, APScheduler scrapers
- `frontend/` — Next.js App Router, Tailwind CSS, NextAuth
- `docker-compose.yml` — local dev stack (postgres, backend, frontend)

## Security (always flag violations)

- Never commit `.env`, `.env.local`, API keys, or secrets
- Never commit the `docs/` folder (private planning docs, gitignored)
- Use `.env.example` files with empty placeholder values only

## PR standards

- Use conventional commits: `feat(backend):`, `feat(frontend):`, `fix:`, `chore:`, `ci:`, `test:`
- Feature branches: `feat/<area>-<description>`
- Every PR must include a test plan and pass CI (backend pytest + import check, frontend lint/build, Docker build)
- **Copilot PR review is optional** — batch changes, run local `pytest` and lint first; request Copilot only for non-trivial changes to conserve premium requests

## Code review focus

- Backend: async patterns, graceful scraper error handling, no blocking I/O in async routes
- Frontend: use `frontend/lib/api.ts` for API calls, `"use client"` on interactive components
- UI: zinc-950 canvas, zinc-900 panels, indigo-600 accent — match existing design system
- Scrapers: inherit `JobSource` from `backend/app/scrapers/base.py`, register in `scraper_runner.py`

## Do not

- Add unnecessary dependencies or over-engineer abstractions
- Break existing API shapes without migration notes
- Remove `AUTH_DISABLED` dev mode bypass in middleware
