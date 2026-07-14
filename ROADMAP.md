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

### Phases 6–9 (original plan) — re-scoped into v0.5

Company watchlist, Gmail import, weekly analytics, and hardening are absorbed into the v0.5 phases below (Gmail import → v0.5 Phase 7, analytics/follow-ups → v0.5 Phase 8, hardening/retention → v0.5 Phase 9, watchlist deferred).

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

## v0.5.0 — Human-in-the-Loop Job-Search OS (In Planning)

Goal: optimize **interview conversion**, not application volume. Every consequential action (submit, outreach, sensitive answers) goes through human approval; every generated claim traces to a verified candidate fact. Detailed specs: `docs/product/` (local planning docs — gitignored).

- [x] Phase 0 (partial) — audit logging + AI provenance (`audit_logs`, `agent_runs` model/prompt/confidence — migration 007)
- [x] Phase 1 (partial) — candidate facts, achievements, career profiles, answer bank tables + facts CRUD behind `FEATURE_CANDIDATE_INTELLIGENCE` (migration 008)
- [ ] Phase 0 (finish) — `application_events` stream + validated lifecycle transitions owned by `user_applications`
- [ ] Phase 1 (finish) — achievements/profiles/answer-bank routes + UI, legacy-profile + resume-text backfill, scorer & resume pipeline read verified facts, prohibited-claim enforcement
- [ ] Phase 1 — GitHub projects import: sync public repos (manual + first-login prompt), per-repo README summaries cached by content hash → confirmed `project` facts → compact projects digest; resume tailor picks 0–2 projects seniority-adaptively (senior roles lean on experience, not side projects)
- [ ] Phase 2 — explainable qualification: `job_requirements` extraction (cached per catalog job), hard blockers, evidence mapping, Tier A/B/C/Reject
- [ ] Phase 3 — application packages: strategy, immutable `document_versions` snapshots, factuality quality gates, `application_answers`
- [ ] Phase 4 — Approval Centre: unified `approval_items` queue, approve/edit/reject/defer, risk-tiered `automation_rules`, daily command centre
- [ ] Phase 5 — application copilot: extension reads form fields on user click, suggests verified answers, flags sensitive fields, human submits
- [ ] Phase 6 — contacts & outreach: manual/extension-captured contacts, drafted messages, follow-up chains with limits + suppression (manual send)
- [ ] Phase 7 — inbox & interview intelligence: forward-address email classification → timeline events, interview workspace with STAR prep
- [ ] Phase 8 — outcome analytics: funnel from events, conversion by source/role-family/strategy, token cost per package
- [ ] Phase 9 — multi-user SaaS hardening (Redis rate limits, retention jobs, monitoring, budget caps)

Non-negotiables: no auto-submission, no CAPTCHA bypass, no unauthorized LinkedIn automation, no fabricated experience, LLM calls gated + cached + structured (token frugality).

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
