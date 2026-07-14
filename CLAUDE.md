# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

JobPilot is an autonomous AI resume builder and job search command centre. The primary feature is a multi-agent AI pipeline that takes a job description, analyzes it, researches the company, tailors the user's resume for ATS optimization, and compiles it to a PDF via LaTeX. Users bring their own LLM API keys (BYOK — OpenAI or Anthropic/Claude).

## Commands

### Local Development (no Docker)
```bash
# Start only PostgreSQL via Docker, run services locally
docker compose up postgres -d
./scripts/dev.sh

# Or manually:
# Backend
cd backend && source .venv/bin/activate
uvicorn app.main:socket_app --reload --port 8000

# Frontend
cd frontend && npm run dev
```

### Docker (full stack)
```bash
docker compose up --build          # dev
docker compose up postgres -d      # just the DB
```

### Backend
```bash
cd backend
source .venv/bin/activate
pip install -r requirements.txt

# Run tests
pytest
pytest tests/test_specific.py::test_name  # single test
pytest tests/integration/test_pipeline.py  # resume pipeline integration tests (mocked LLM, no DB)

# Lint (none configured; use ruff if needed)
```

To verify the whole AI resume + cover-letter loop (tests + real PDF render + optional real LLM
run) in one shot, run the `/verify-resume-pipeline` skill (`.claude/skills/verify-resume-pipeline/`).

### Frontend
```bash
cd frontend
npm install
npm run dev       # http://localhost:3000
npm run build
npm run lint
```

### Tectonic (LaTeX → PDF)
```bash
./scripts/ensure-tectonic.sh   # downloads to backend/.bin/tectonic
```

## Architecture

### Monorepo Layout
```
JobPilot/
├── backend/          # FastAPI Python app
├── frontend/         # Next.js 14 App Router TypeScript app
├── extension/        # Chrome extension (capture jobs)
├── scripts/          # Dev helpers
└── docker-compose.yml
```

### Backend (`backend/app/`)

**Entry point:** `main.py` — mounts all routers under `/api/v1/`, attaches Socket.IO as an ASGI sub-app (`socket_app`), and runs Alembic migrations + DB init on startup.

**Key subsystems:**

| Path | Purpose |
|------|---------|
| `agents/graph.py` | Multi-agent pipeline: `ingest_context → analyze_jd → research_company → tailor_resume → cover_letter → ats_score`. Runs as FastAPI `BackgroundTasks`. Emits Socket.IO events per step. |
| `agents/editor_agent.py` | LLM-powered in-editor chat — proposes `PendingChange` diffs for the 3-pane editor |
| `services/llm/client.py` | BYOK LLM client — reads per-user encrypted API key from DB, creates `langchain` chat model |
| `services/resume/pdf_compiler.py` | Compiles LaTeX to PDF via `tectonic` binary. Falls back to a minimal plain-text PDF if Tectonic is missing. |
| `services/resume/renderer.py` | Renders `ResumeContent` JSON → Jake's Resume LaTeX template |
| `services/ats/scorer.py` | ATS scoring: keyword match + formatting + semantic + skills coverage |
| `services/rag/` | pgvector-based RAG: chunk and embed profile/JD/company text, semantic search for tailoring |
| `jobs/pipeline/` | Job ingestion pipeline (scraping, dedup, normalizing) |
| `jobs/scoring/` | Job fit scoring engine for the Inbox |
| `scrapers/` | Job board scrapers (RemoteOK, WeWorkRemotely, HackerNews) + URL importer (Playwright) |
| `core/config.py` | All env vars via `pydantic-settings` |
| `core/database.py` | Async SQLAlchemy engine + session |
| `sockets/chat.py` | Socket.IO event handlers (resume pipeline progress + community chat) |

**Pipeline flow (resume generation):**
1. `POST /api/v1/resumes` creates a `ResumeDocument` in DB with `status=processing`
2. `run_generation_pipeline()` runs in background: 5 sequential LLM steps
3. Each step emits `agent_step` Socket.IO events to room `resume:{id}`
4. On completion: writes `content_json` (structured), `latex_source`, `ats_result` to DB
5. PDF is compiled on-demand at `GET /api/v1/resumes/{id}/pdf`

**Auth:** `AUTH_DISABLED=true` in `.env` bypasses JWT for local dev. In production, NextAuth issues JWTs, backend verifies via `SECRET_KEY`.

### Frontend (`frontend/`)

**Routing:** Next.js App Router with two route groups:
- `app/(marketing)/` — public landing page at `/`
- `app/(dashboard)/` — authenticated shell with sidebar; all feature pages

**Key pages/components:**

| Path | Purpose |
|------|---------|
| `app/(dashboard)/resumes/new/page.tsx` | Create resume form — paste JD, optionally add company URL + cover letter meta |
| `app/(dashboard)/resumes/[id]/page.tsx` | 3-pane editor: AI chat + LaTeX editor + PDF preview |
| `components/resume/PipelineProgressBar.tsx` | Socket.IO progress display during generation |
| `components/resume/LatexEditor.tsx` | CodeMirror LaTeX editor |
| `components/resume/PdfPreviewPane.tsx` | Embeds PDF preview via iframe to backend `/pdf` endpoint |
| `components/resume/StructuredEditor.tsx` | Form-based section editor for `content_json` fields |
| `lib/api.ts` | Typed fetch wrapper for all backend calls |
| `lib/llmPresets.ts` | LLM model presets for the Settings dropdown |
| `middleware.ts` | Route protection (redirects unauthenticated users) |

**Socket.IO:** Frontend connects to backend and joins room `resume:{id}` on editor load to receive real-time pipeline step events.

### Database

PostgreSQL 15 + pgvector. Key tables:
- `users` — OAuth + profile data + encrypted LLM API keys
- `user_profile_structured` — structured JSON profile (experience, education, skills, projects)
- `resume_documents` — resume records with `content_json` (structured), `latex_source`, `insights_json`, `status`
- `ats_scores` — ATS score history per resume
- `pending_changes` + `chat_messages` — editor AI chat diffs
- `jobs` + `user_applications` — job board + Kanban tracker
- `inbox_jobs` — Job Intelligence inbox (v0.4)
- `rag_chunks` — pgvector embeddings for RAG

Schema is managed by Alembic (`backend/alembic/`) but `main.py` also runs `CREATE TABLE IF NOT EXISTS` / `ALTER TABLE ADD COLUMN IF NOT EXISTS` guards on startup.

## Environment Variables

### Backend (`backend/.env`) — critical ones

| Variable | Purpose |
|----------|---------|
| `DATABASE_URL` | `postgresql+asyncpg://...` |
| `SECRET_KEY` | JWT signing + BYOK AES encryption |
| `AUTH_DISABLED` | `true` for local dev (no OAuth) |
| `TECTONIC_PATH` | Optional path to tectonic binary; auto-detected from `backend/.bin/tectonic` |
| `ALLOWED_ORIGINS` | CORS origins (comma-separated) |
| `FEATURE_CANDIDATE_INTELLIGENCE` | `true` enables `/api/v1/candidate/*` and facts-based scoring/resume generation; default `false` (all candidate routes 404 when off) |

Users configure their own LLM keys in Settings UI — no provider key needed in server env.

### Frontend (`frontend/.env.local`) — critical ones

| Variable | Purpose |
|----------|---------|
| `NEXT_PUBLIC_API_URL` | Backend URL (`http://localhost:8000`) |
| `AUTH_DISABLED` / `NEXT_PUBLIC_AUTH_DISABLED` | `true` skips OAuth in dev |
| `NEXTAUTH_URL` + `NEXTAUTH_SECRET` | NextAuth config |
| `GITHUB_ID` / `GITHUB_SECRET` | GitHub OAuth (required in production) |

## Resume Pipeline — Key Invariants

- The pipeline only runs if the user has a BYOK LLM key configured in Settings. Without one, it falls back to the profile data as-is.
- `content_json` is a `ResumeContent` Pydantic schema (`backend/app/schemas/resume_content.py`) — JSON with sections: `contact`, `summary`, `experience`, `education`, `skills`, `projects`.
- The guard (`agents/validation.py`) prevents the LLM from adding fabricated data — it compares source vs tailored content and strips any added employers, metrics, or dates.
- Tectonic must be installed for real PDF compilation. Run `./scripts/ensure-tectonic.sh` once. The fallback PDF is plain-text only.
- ATS scoring uses multi-dimensional scoring: keyword match (TF-IDF), formatting score, semantic score (via LLM), skills coverage.

## Candidate Intelligence (v0.5 Phase 1, behind `FEATURE_CANDIDATE_INTELLIGENCE`)

- Source of truth: `candidate_facts` (typed payloads validated via `PAYLOAD_MODELS` in `backend/app/schemas/candidate.py`), plus `achievements`, `career_profiles`, `answer_bank_entries`, and the derived `candidate_digests` cache (migrations 008–009).
- Services in `backend/app/services/candidate/` (facts, achievements, career_profiles, answer_bank, backfill, extraction, imports, github_import, digest, resume_source, project_selection); routes in `backend/app/api/routes/candidate.py`.
- Imports return **drafts** for review; only `POST /candidate/import/confirm` persists (as unverified). GitHub sync caches per-repo README summaries by sha in `candidate_digests.sync_state_json` — unchanged repos cost zero LLM tokens on re-sync.
- With the flag on: the fit scorer prefers verified facts (`build_candidate_profile_with_source`; source logged in `job_fit_scores.signals._meta`), the resume pipeline builds content from **user-confirmed** facts only, projects are selected seniority-adaptively (`project_selection.py`: junior ≤2, mid gap-fill only, senior ≤1), and `agents/validation.py` strips project bullets lacking a confirmed `evidence_fact_id` plus any prohibited-claim content.
- Answer-bank sensitivity (`salary`, `work_authorization`, `demographic`, `legal_declaration`) is derived server-side and cannot be unset by clients.

## Do Not Commit

- `backend/.env`, `frontend/.env.local`, `docs/` folder (per `.cursor/rules/jobpilot-core.mdc`)
