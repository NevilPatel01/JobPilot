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

JobPilot uses **GitHub Copilot** for PR workflows and code review. Copilot reads project rules from:

- `.github/copilot-instructions.md` — repo-wide standards
- `.github/instructions/*.instructions.md` — path-specific rules (backend, frontend, CI)

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

### Request Copilot code review

After the PR is open, request a review using one of these methods:

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
- [ ] Backend changes tested via API or pytest
- [ ] Frontend changes pass `npm run lint` and `npm run build`
- [ ] PR description includes summary and test plan
- [ ] Copilot code review requested and feedback addressed

## Code Style

- **Python**: async-first, type hints, follow existing patterns in `backend/app/`
- **TypeScript**: strict mode, client components marked with `"use client"`
- **UI**: dark mode zinc/indigo palette per existing components

## Questions?

Open a [GitHub Issue](https://github.com/NevilPatel01/JobPilot/issues) for bugs or feature requests.
