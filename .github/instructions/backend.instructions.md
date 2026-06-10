---
applyTo: "backend/**/*.py"
---

# Backend (Python / FastAPI)

- Use async SQLAlchemy via `get_db` dependency from `app.core.database`
- Mount routes under `/api/v1/` in `app.main.py`
- Pydantic schemas in `app/api/schemas.py`
- New scrapers: inherit `JobSource`, implement `async def fetch()`, register in `SCRAPERS` list
- On scraper failure: log and return `[]`, never crash the batch runner
- Deduplication: `get_dedup_hash(title, company)` before insert
- JWT auth via `get_current_user` in `app.core.auth`; respect `AUTH_DISABLED` setting
