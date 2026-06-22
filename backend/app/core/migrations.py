"""Alembic migration bootstrap for application startup."""

import logging
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.core.config import settings

logger = logging.getLogger(__name__)


def run_alembic_migrations() -> None:
    """Apply pending Alembic revisions. Safe to call on every startup."""
    backend_root = Path(__file__).resolve().parents[2]
    cfg = Config(str(backend_root / "alembic.ini"))
    cfg.set_main_option("script_location", str(backend_root / "alembic"))
    cfg.set_main_option("sqlalchemy.url", settings.database_url.replace("+asyncpg", ""))
    logger.info("Running Alembic migrations")
    command.upgrade(cfg, "head")
    logger.info("Alembic migrations complete")
