---
name: verify-resume-pipeline
description: Verify the JobPilot AI resume + cover-letter builder works end to end — runs the backend test suite, the mocked-LLM pipeline integration tests, and a real JSON→LaTeX→PDF render. Use when asked to check/verify/smoke-test the resume builder, ATS scoring, or PDF generation, or before deploying.
---

# Verify the Resume / Cover-Letter Pipeline

Use this to confirm the core loop (job description → tailored, ATS-scored, PDF-ready resume)
is healthy after changes or before a deploy.

## 1. Backend test suite (fast, no DB needed)

```bash
cd backend && source .venv/bin/activate && python -m pytest -q
```

Expect all tests green. The pipeline-specific coverage lives in
`tests/integration/test_pipeline.py` (step order, fabrication guard, content/LaTeX/ATS
persistence, tailor-only mode, failure path, JSON→LaTeX→PDF smoke) and the unit tests
`test_validation.py`, `test_renderer.py`, `test_ats_scorer.py`, `test_cover_letter_*`.

If you only want the pipeline tests:

```bash
cd backend && source .venv/bin/activate && python -m pytest tests/integration/test_pipeline.py -v
```

## 2. Confirm real PDF compilation (Tectonic)

```bash
cd backend && source .venv/bin/activate && python -c "
from app.services.resume.renderer import render_resume_latex
from app.services.resume.pdf_compiler import compile_latex_to_pdf_with_status
import json
r = json.load(open('tests/fixtures/sample_resume.json'))
b, fb = compile_latex_to_pdf_with_status(render_resume_latex(r))
print('pdf_bytes=', len(b), 'used_fallback=', fb)
assert b.startswith(b'%PDF')
"
```

- `used_fallback=False` → Tectonic compiled a styled PDF (good).
- `used_fallback=True` → Tectonic missing/failing; run `./scripts/ensure-tectonic.sh`. The app
  still serves a plain-text fallback PDF and sets the `X-PDF-Fallback: true` response header on
  `GET /resumes/{id}/pdf`.

## 3. Optional: real LLM end-to-end run

A genuinely *tailored* resume needs a decryptable BYOK key. Check presence (never print key bytes):

```bash
cd backend && source .venv/bin/activate && python -c "
import asyncio
from app.core.database import async_session
from app.services.llm.client import get_user_llm_config
from sqlalchemy import text
async def main():
    async with async_session() as db:
        r = await db.execute(text('SELECT id, email FROM users ORDER BY created_at'))
        for uid, email in r.fetchall():
            cfg = await get_user_llm_config(db, str(uid))
            print(email, '-> provider=', cfg.provider if cfg else None, 'has_key=', bool(cfg and cfg.api_key))
asyncio.run(main())
"
```

If it logs `Skipping API key that cannot be decrypted`, the `SECRET_KEY` in `backend/.env`
differs from the one used when the key was saved — the user must re-enter their LLM key in
**Settings** for real tailoring to work (otherwise the pipeline silently falls back to the
profile as-is). With a decryptable key present:

```bash
docker compose up postgres -d
./scripts/ensure-tectonic.sh
cd backend && source .venv/bin/activate && AUTH_DISABLED=true uvicorn app.main:socket_app --port 8000
# then POST a job description to /api/v1/resumes, poll GET /api/v1/resumes/{id}/status,
# and GET /api/v1/resumes/{id}/pdf — confirm a tailored PDF + ATS score.
```

## 4. Frontend contract

```bash
cd frontend && npm run lint && npm run build
```

Confirms the `frontend/lib/api/` client and the resume editor pages still compile.

## Pass criteria
- Backend `pytest` fully green (includes the 6 pipeline integration tests).
- Step-2 render prints `%PDF` bytes (ideally `used_fallback=False`).
- Frontend `lint` + `build` succeed.
- If a real key is decryptable, a real run yields a tailored resume PDF with a non-zero ATS score.
