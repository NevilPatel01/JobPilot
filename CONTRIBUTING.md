# Contributing to JobPilot

Thank you for your interest in contributing! JobPilot is free and open-source — community contributions make it better for everyone.

## Getting Started

1. Fork the repository
2. Clone your fork: `git clone https://github.com/YOUR_USERNAME/JobPilot.git`
3. Create a feature branch: `git checkout -b feat/your-feature`
4. Make your changes
5. Run tests and linting (see below)
6. Open a pull request against `main`

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

## Code Style

- **Python**: async-first, type hints, follow existing patterns in `backend/app/`
- **TypeScript**: strict mode, client components marked with `"use client"`
- **UI**: dark mode zinc/indigo palette per existing components

## Questions?

Open a [GitHub Issue](https://github.com/NevilPatel01/JobPilot/issues) for bugs or feature requests.
