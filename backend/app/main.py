from contextlib import asynccontextmanager

import socketio
from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import analytics, applications, auth, jobs, profile, scraper
from app.api.schemas import HealthResponse
from app.core.config import settings
from app.core.database import Base, engine
from app.core.scheduler import start_scheduler
from app.sockets.chat import sio

health_router = APIRouter()


@health_router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", version="1.0.0")


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.run_sync(Base.metadata.create_all)


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

socket_app = socketio.ASGIApp(sio, other_asgi_app=app)
