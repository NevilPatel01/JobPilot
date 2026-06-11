from contextlib import asynccontextmanager

import socketio
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import analytics, applications, auth, cover_letters, documents_api, jobs, profile, resumes, scraper, settings
from app.api.schemas import HealthResponse
from app.core.config import settings
from app.core.database import Base, engine
from app.core.scheduler import start_scheduler
from app.services.location import TARGET_COUNTRY, detect_country
from app.sockets.chat import sio

health_router = APIRouter()


@health_router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="1.0.0")


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("ALTER TABLE jobs ADD COLUMN IF NOT EXISTS country VARCHAR(2)"))
        await conn.execute(text("CREATE INDEX IF NOT EXISTS ix_jobs_country ON jobs (country)"))

        for col, col_type in (
            ("semantic_score", "INTEGER DEFAULT 0"),
            ("skills_coverage", "INTEGER DEFAULT 0"),
            ("section_score", "INTEGER DEFAULT 0"),
            ("matched_keywords", "JSONB"),
            ("breakdown_json", "JSONB"),
        ):
            await conn.execute(text(f"ALTER TABLE ats_scores ADD COLUMN IF NOT EXISTS {col} {col_type}"))

        rows = await conn.execute(
            text(
                """
                SELECT id, location, title, description
                FROM jobs
                WHERE country IS NULL
                """
            )
        )
        for job_id, location, title, description in rows:
            country = detect_country(location, description or "", title or "")
            await conn.execute(
                text("UPDATE jobs SET country = :country WHERE id = :id"),
                {"country": country, "id": job_id},
            )

        await conn.execute(
            text(
                """
                UPDATE jobs
                SET is_active = false
                WHERE is_active = true
                  AND (country IS NULL OR country != :country)
                """
            ),
            {"country": TARGET_COUNTRY},
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    start_scheduler()
    yield


app = FastAPI(title="JobPilot API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(jobs.router, prefix="/api/v1/jobs", tags=["jobs"])
app.include_router(applications.router, prefix="/api/v1/applications", tags=["applications"])
app.include_router(scraper.router, prefix="/api/v1/scraper", tags=["scraper"])
app.include_router(profile.router, prefix="/api/v1/profile", tags=["profile"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])
app.include_router(settings.router, prefix="/api/v1/settings", tags=["settings"])
app.include_router(resumes.router, prefix="/api/v1/resumes", tags=["resumes"])
app.include_router(cover_letters.router, prefix="/api/v1/cover-letters", tags=["cover-letters"])
app.include_router(documents_api.router, prefix="/api/v1/documents", tags=["documents-api"])

socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
