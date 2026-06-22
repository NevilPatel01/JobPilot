# JobPilot Roadmap

## v0.1.x — MVP (Shipped)

- [x] FastAPI backend with PostgreSQL + pgvector
- [x] Job scrapers: RemoteOK, WeWorkRemotely, Hacker News
- [x] Smart deduplication by title + company
- [x] Daily CRON scrape (02:00 UTC)
- [x] Kanban application tracker with drag-and-drop
- [x] URL-based job importer (Playwright)
- [x] Resume match scoring (TF-IDF)
- [x] Analytics dashboard (Chart.js)
- [x] AI resume builder — multi-agent RAG, LaTeX/Tectonic PDF, ATS scoring
- [x] Premium dark UI (Linear-inspired)
- [x] Docker Compose dev environment
- [x] Google + GitHub OAuth
- [x] Public API with API keys

---

## v0.4.0 — Job Intelligence + Capture (Ready to Build)

> **Plan:** [JOB_INTELLIGENCE_PLAN.md](./JOB_INTELLIGENCE_PLAN.md)
> **Decisions:** [JOB_INTELLIGENCE_QUESTIONS.md](./JOB_INTELLIGENCE_QUESTIONS.md) (answered)
> **Source repo:** [canada-tech-job-market-analysis-2026](https://github.com/NevilPatel01/canada-tech-job-market-analysis-2026)
> **Database:** PostgreSQL + pgvector only (no Supabase)

**North star:** Apply faster to higher-fit Canadian technical jobs in AB/BC/ON/SK and get interviews — not maximize job volume.

### Phase 1 — Inbox + Normalized Model + Manual Import

- [x] Alembic `002_job_intelligence` migration
- [x] `NormalizedJob` contract + ingestion pipeline (normalize → dedup v2 → persist)
- [x] **Job Inbox** API + UI (`/inbox`)
- [x] Inbox statuses: new, ai_reviewed, shortlisted, resume_ready, applied, archived, duplicate
- [x] Manual paste + URL import → same pipeline
- [x] Stop auto-creating `user_applications` from scrapes
- [x] User scoring prefs: work permit, target provinces (AB, BC, ON, SK)
- [x] Tests: dedup, normalization

### Phase 2 — Fit Scoring Engine

- [x] Explainable weighted profile + rules scorer (0–100), ready for optional AI enrichment
- [x] Thresholds: &lt;40 low, 40–59 stretch, 60–74 reviewed, 75–84 recommended, 85+ priority
- [x] Risk flags: senior-only, non-Canada, unrealistic experience, low skill match
- [x] Resume category recommender (5 categories)
- [x] Inbox filters + fit columns
- [x] Tests: scoring engine

### Phase 3 — Resume Generate from Inbox

- [x] Seed resume category templates (from profile — truthful only)
- [x] `ai_recommended_category` + `user_selected_category` on inbox jobs
- [x] "Generate Tailored Resume" from shortlisted inbox job
- [x] Link resume ↔ inbox ↔ tracker; "why this resume version"
- [x] Tests: resume linkage

### Phase 4 — Canadian Source Adapters

- [x] Port Job Bank, Adzuna, JSearch from old repo
- [x] Instance-level API keys in `.env` with graceful fallback + Source Settings UI
- [x] `job_sources` config, `scraper_runs` audit log
- [x] Role priority queue when rate-limited (IT Support → App Support → Cloud first)
- [x] Scheduler: 08:00 + optional 18:00 America/Toronto
- [x] Tests: source normalization fixtures

### Phase 5 — Chrome Extension

- [x] `extension/` — JobPilot Capture (MV3, unpacked dev)
- [x] Capture API endpoint (`X-API-Key`)
- [x] Extension setup page (`/extension`)
- [x] Tests: extension capture endpoint

### Phase 6 — Company Watchlist + Boards

- [ ] Greenhouse + Lever + custom career page adapters
- [ ] Watchlist UI + seed companies (banks, Shopify, HHS, universities, etc.)
- [ ] Ashby if straightforward

### Phase 7 — Gmail Forward Import

- [ ] Inbound email parser (`jobs+token@…`)
- [ ] MVP: LinkedIn, Indeed, Job Bank, recruiter emails
- [ ] Gmail import setup page (`/gmail-import`)

### Phase 8 — Weekly Analytics Report

- [ ] Application events timeline
- [ ] Job analytics: response rate, best sources/cities/resume categories
- [ ] Weekly report page + in-app follow-up reminders (5d / 10d business days)
- [ ] Tracker sync summary on inbox items

### Phase 9 — Production Hardening + Gmail OAuth

- [ ] GitHub Actions scrape workflow (backup to APScheduler)
- [ ] Data retention jobs (180d catalog, 45d inbox archive, raw_payload prune)
- [ ] Per-user API keys (BYOK for Adzuna/JSearch)
- [ ] Gmail OAuth label import (later)
- [ ] Deprecate legacy `app/scrapers/` layout

### New UI Pages

| Page | Route |
|------|-------|
| Job Inbox | `/inbox` |
| Saved Searches | `/saved-searches` |
| Source Settings | `/sources` |
| Company Watchlist | `/watchlist` |
| Extension Setup | `/extension` |
| Gmail Import | `/gmail-import` |
| Scraper Runs | `/scraper-runs` |
| Job Analytics | `/job-analytics` |

### Explicit Non-Goals

- Supabase migration
- Aggressive LinkedIn/Indeed scraping
- Removing existing resume builder or Kanban
- Separate Streamlit app

---

## v0.2.0 — Community (Deferred)

- [ ] Subreddit-style forums by topic
- [ ] Real-time chat rooms (Socket.io)
- [ ] Moderation system (pin, remove, roles)
- [ ] Public/private channels

---

## v0.3.0 — Notifications (Partially Absorbed by v0.4)

- [ ] Weekly job expiry checker (Playwright)
- [ ] "Last verified" badge on listings
- [ ] In-app notifications (follow-ups in v0.4)
- [ ] Browser push notifications for job matches
- [ ] Saved searches with alerts → v0.4 Job Inbox

---

## v1.0.0 — OSS Polish

- [ ] Full Alembic migration history (incl. job intelligence)
- [ ] Comprehensive test coverage
- [ ] Production Docker Compose with Nginx
- [ ] Source plugin documentation
- [ ] GitHub Actions CI/CD

---

## Post v1.0 Ideas

- Natural-language job search (RAG over inbox catalog)
- Salary insights (community-sourced)
- Interview question bank
- Email digest notifications
