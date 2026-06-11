# Contributing to JobPilot

Thank you for your interest in contributing! JobPilot is free and open-source — community contributions make it better for everyone.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/JobPilot.git`
3. Create a feature branch: `git checkout -b feat/your-feature`
4. Make your changes
5. Run tests and linting (see below)
6. Open a pull request against `main`

## Pull requests with GitHub Copilot

JobPilot can use **GitHub Copilot** for optional PR code review. Copilot reads project rules from:

- `.github/copilot-instructions.md` — repo-wide standards
- `.github/instructions/*.instructions.md` — path-specific rules (backend, frontend, CI)

### Minimize Copilot usage (recommended)

Copilot PR reviews consume GitHub Copilot premium requests. To use credits efficiently:

1. **Run local checks first** — `pytest` in `backend/`, `npm run lint && npm run build` in `frontend/`
2. **Batch related changes** — one focused PR per feature slice instead of many tiny PRs
3. **Skip Copilot review when** CI is green, changes are test-only (`test:`, `ci:`), or you self-reviewed against `copilot-instructions.md`
4. **Request Copilot review when** the PR touches auth, scrapers, LLM pipeline, or DB migrations and you want a second pass

Maintainers may merge without Copilot when CI passes and the test plan is complete.

### Opening a PR (GitHub CLI)

```bash
git push -u origin feat/your-feature

gh pr create --title "feat(backend): short description" --body "$(cat <<'EOF'
## Summary
- What changed and why

## Test plan
- [ ] docker compose up
- [ ] Relevant API or UI tested

## Checklist
- [ ] No secrets committed
- [ ] CI passes
EOF
)"
```

### Request Copilot code review (optional)

Use Copilot review when you want automated feedback on non-trivial changes. Skip for test-only or docs-only PRs if CI is green.

**GitHub CLI v2.88+:**
```bash
gh pr edit --add-reviewer @copilot
```

**GitHub API (works on any gh version):**
```bash
gh api --method POST repos/NevilPatel01/JobPilot/pulls/PR_NUMBER/requested_reviewers \
  -f 'reviewers[]=copilot-pull-request-reviewer[bot]'
```

**GitHub web UI:**
1. Open the PR → click **Reviewers**
2. Select **Copilot**

Fix any issues Copilot flags, then push updates. Copilot reviews use instruction files on the **base branch** (`main`).

### CI must pass before merge

GitHub Actions runs on every PR:

- Backend import verification
- Frontend `npm run lint` and `npm run build`
- Docker image builds

Check status: `gh pr checks <PR_NUMBER>`

## Branch Naming

| Prefix | Use for |
|--------|---------|
| `feat/` | New features |
| `fix/` | Bug fixes |
| `chore/` | Tooling, deps, config |
| `ci/` | CI/CD changes |
| `docs/` | Documentation only |

## Adding a New Job Scraper

The most impactful contribution type:

1. Create `backend/app/scrapers/yoursource.py`
2. Inherit from `JobSource` (see `backend/app/scrapers/base.py`)
3. Set `source_name = "yoursource"`
4. Implement `async def fetch(self) -> list[RawJob]`
5. Register in `backend/app/services/scraper_runner.py` → `SCRAPERS` list
6. Handle errors gracefully — return `[]` on failure
7. Open a PR with a test note (how many jobs fetched)

## PR Checklist

- [ ] No secrets, `.env` files, or `docs/` folder committed
- [ ] Conventional commit messages (`feat(backend):`, `feat(frontend):`, etc.)
- [ ] Backend changes tested via `pytest` (see `backend/requirements-dev.txt`) or manual API check
- [ ] Frontend changes pass `npm run lint` and `npm run build`
- [ ] PR description includes summary and test plan
- [ ] Copilot review requested **if needed** (optional when CI passes and changes are small/test-only)

## Code Style

- **Python**: async-first, type hints, follow existing patterns in `backend/app/`
- **TypeScript**: strict mode, client components marked with `"use client"`
- **UI**: dark mode zinc/indigo palette per existing components

## Pipeline durability

Resume and cover letter generation runs as **in-process background tasks** (FastAPI `BackgroundTasks`), not a durable job queue.

### Current behavior

| Topic | Behavior |
|-------|----------|
| **Execution model** | `POST /resumes` or `POST /api/v1/documents/resumes` returns immediately with `status: processing`. The multi-agent pipeline runs after the HTTP response. |
| **Progress** | Steps stream over Socket.IO (`agent_step`, `agent_complete`, `agent_error`). The public API can poll `GET /documents/resumes/{id}` or supply an optional `webhook_url` on create. |
| **Server restart** | Background tasks are **not persisted**. If the API process restarts while a job is `processing`, that work is lost. The document may remain stuck in `processing` until the stale-job sweeper marks it failed (~30 minutes) or an operator calls regenerate. |
| **Per-step retries** | LLM calls use bounded retries/timeouts (`app/agents/retry.py`). A failed step records `pipeline_error` and `last_step` on the resume. |
| **Recovery** | Use regenerate endpoints: `POST /resumes/{id}/regenerate` (full pipeline), `POST /resumes/{id}/regenerate/resume` (tailor + ATS only), or `POST /cover-letters/{id}/regenerate`. Cached JD/company analysis is reused when possible. |
| **Logging** | Pipeline steps emit structured logs with `resume_id`, `step`, and `duration_ms` for ops dashboards. |

### BackgroundTasks limitations

- Tasks live only in the running process memory.
- No cross-worker coordination (multiple Uvicorn workers would each run independent task queues).
- No automatic retry after process crash — operators or integrators must call regenerate.
- Long-running pipelines block a thread pool slot in the worker (acceptable at current scale).

### Planned: durable queue (ARQ or Celery)

For production deployments with restarts, horizontal scaling, or strict SLAs, a follow-up change should move pipeline execution to a **durable queue**:

1. **Enqueue** on create/regenerate with `resume_id` and `mode` (`full`, `tailor_only`, `cover_letter_only`).
2. **Worker process** runs `run_generation_pipeline()` with the same step graph in `app/agents/graph.py`.
3. **Redis** (ARQ) or **RabbitMQ/Redis** (Celery) as the broker; PostgreSQL remains the source of truth for document state.
4. **Idempotency**: skip or resume from `last_step` when a job is re-queued.
5. **Webhook + Socket.IO** unchanged — emit from the worker after commit.

ARQ fits the existing async stack; Celery is preferable if you already run Celery workers elsewhere. Until then, self-hosters should plan for occasional regenerate after deploys and use `webhook_url` or polling in integrations.

## Questions?

Open a [GitHub Issue](https://github.com/NevilPatel01/JobPilot/issues) for bugs or feature requests.
