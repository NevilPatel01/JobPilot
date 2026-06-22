import logging
import time
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.jobs.pipeline.ingest import ingest_job
from app.jobs.pipeline.normalizer import normalize_raw_job
from app.jobs.sources.base import SourceAuthError, SourceRateLimited
from app.jobs.sources.registry import SOURCE_DEFINITIONS, credential_status, ensure_source_configs
from app.models.job import Job
from app.models.job_intelligence import JobSourceConfig, ScraperRun
from app.models.user import User
from app.scrapers.hackernews import HackerNewsScraper
from app.scrapers.remoteok import RemoteOKScraper
from app.scrapers.weworkremotely import WeWorkRemotelyScraper
from app.services.job_filters import apply_canada_filter

logger = logging.getLogger(__name__)

ROLE_PRIORITY = (
    "IT Support",
    "Application Support",
    "Cloud Support Junior DevOps",
    "Full Stack Web Developer",
    "Automation SCADA",
    "Quality Assurance",
    "Data Analyst",
)
DEFAULT_LOCATIONS = (
    "Hamilton", "Calgary", "Regina", "Vancouver", "Toronto", "Saskatoon",
    "Kitchener", "Waterloo", "Ottawa", "Mississauga", "Oakville", "Burlington",
)
LEGACY_SCRAPERS = {
    scraper.source_name: scraper
    for scraper in (RemoteOKScraper(), WeWorkRemotelyScraper(), HackerNewsScraper())
}

_scraper_status = {"status": "idle", "last_run": None, "last_new_jobs": 0, "error": None}
_last_manual_run: datetime | None = None


def get_scraper_status() -> dict:
    return _scraper_status.copy()


def build_query_queue(limit: int) -> list[tuple[str, str]]:
    first_wave_cities = DEFAULT_LOCATIONS[:4]
    queue = [(role, city) for role in ROLE_PRIORITY[:3] for city in first_wave_cities]
    queue.extend(
        (role, city)
        for role in ROLE_PRIORITY
        for city in DEFAULT_LOCATIONS
        if (role, city) not in queue
    )
    return queue[: max(0, limit)]


async def _record_skipped(
    session: AsyncSession,
    source: str,
    error: str,
    *,
    dry_run: bool,
) -> None:
    session.add(
        ScraperRun(
            source=source,
            status="skipped",
            errors=[error],
            dry_run=dry_run,
            completed_at=datetime.now(timezone.utc),
        )
    )


async def _run_modern_source(
    session: AsyncSession,
    config: JobSourceConfig,
    *,
    dry_run: bool,
) -> int:
    definition = SOURCE_DEFINITIONS[config.name]
    adapter = definition.adapter()
    if not adapter.credentials_available:
        message = f"Missing credentials for {definition.display_name}"
        config.last_error = message
        await _record_skipped(session, config.name, message, dry_run=dry_run)
        await session.commit()
        return 0

    users = (await session.execute(select(User))).scalars().all()
    total_new = 0
    async with adapter:
        for query, city in build_query_queue(settings.scraper_max_queries_per_source):
            started = time.perf_counter()
            run = ScraperRun(source=config.name, query=query, city=city, status="running", dry_run=dry_run)
            session.add(run)
            await session.flush()
            try:
                jobs = await adapter.fetch(query, city, settings.scraper_max_pages)
                target_jobs = [
                    job for job in jobs
                    if job.province in settings.target_province_codes or job.remote_type == "remote"
                ]
                new_count = 0
                duplicate_count = 0
                if not dry_run:
                    for job in target_jobs:
                        if users:
                            first_result = None
                            for user in users:
                                result = await ingest_job(
                                    session,
                                    job,
                                    user_id=user.id,
                                    captured_via=config.name,
                                )
                                first_result = first_result or result
                            if first_result and first_result.created:
                                new_count += 1
                            elif first_result:
                                duplicate_count += 1
                        else:
                            result = await ingest_job(session, job)
                            new_count += int(result.created)
                            duplicate_count += int(not result.created)
                run.status = "success"
                run.fetched_count = len(target_jobs)
                run.new_count = new_count
                run.duplicate_count = duplicate_count
                config.last_success = datetime.now(timezone.utc)
                config.last_error = None
                total_new += new_count
            except SourceRateLimited as exc:
                run.status = "rate_limited"
                run.errors = [str(exc)]
                config.last_error = str(exc)
                run.completed_at = datetime.now(timezone.utc)
                run.duration_ms = round((time.perf_counter() - started) * 1000)
                await session.commit()
                break
            except Exception as exc:
                run.status = "failed"
                run.errors = [str(exc)]
                config.last_error = str(exc)
                logger.warning("Source %s query failed: %s", config.name, exc)
            run.completed_at = datetime.now(timezone.utc)
            run.duration_ms = round((time.perf_counter() - started) * 1000)
            await session.commit()
    return total_new


async def _run_legacy_source(
    session: AsyncSession,
    config: JobSourceConfig,
    *,
    dry_run: bool,
) -> int:
    started = time.perf_counter()
    run = ScraperRun(source=config.name, query="Canada", status="running", dry_run=dry_run)
    session.add(run)
    await session.flush()
    try:
        jobs = await LEGACY_SCRAPERS[config.name].fetch()
        new_count = 0
        duplicate_count = 0
        if not dry_run:
            users = (await session.execute(select(User))).scalars().all()
            for raw_job in jobs:
                normalized = normalize_raw_job(raw_job, config.name)
                if users:
                    first_result = None
                    for user in users:
                        result = await ingest_job(
                            session,
                            normalized,
                            user_id=user.id,
                            captured_via=config.name,
                        )
                        first_result = first_result or result
                    new_count += int(bool(first_result and first_result.created))
                    duplicate_count += int(bool(first_result and not first_result.created))
                else:
                    result = await ingest_job(session, normalized)
                    new_count += int(result.created)
                    duplicate_count += int(not result.created)
        run.status = "success"
        run.fetched_count = len(jobs)
        run.new_count = new_count
        run.duplicate_count = duplicate_count
        config.last_success = datetime.now(timezone.utc)
        config.last_error = None
    except Exception as exc:
        run.status = "failed"
        run.errors = [str(exc)]
        config.last_error = str(exc)
        new_count = 0
    run.duration_ms = round((time.perf_counter() - started) * 1000)
    run.completed_at = datetime.now(timezone.utc)
    await session.commit()
    return new_count


async def run_all_scrapers(
    source_names: list[str] | None = None,
    *,
    dry_run: bool | None = None,
) -> int:
    global _scraper_status
    effective_dry_run = settings.scraper_dry_run if dry_run is None else dry_run
    _scraper_status = {"status": "running", "last_run": None, "last_new_jobs": 0, "error": None}
    total_new = 0
    try:
        async with AsyncSessionLocal() as session:
            configs = await ensure_source_configs(session)
            await session.commit()
            selected = source_names or list(SOURCE_DEFINITIONS)
            for name in selected:
                config = configs.get(name)
                definition = SOURCE_DEFINITIONS.get(name)
                if not config or not definition or not config.enabled:
                    continue
                if definition.adapter:
                    total_new += await _run_modern_source(session, config, dry_run=effective_dry_run)
                elif name in LEGACY_SCRAPERS:
                    total_new += await _run_legacy_source(session, config, dry_run=effective_dry_run)
        _scraper_status = {
            "status": "idle",
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_new_jobs": total_new,
            "error": None,
        }
    except Exception as exc:
        logger.exception("Scraper run failed")
        _scraper_status = {
            "status": "error",
            "last_run": datetime.now(timezone.utc).isoformat(),
            "last_new_jobs": total_new,
            "error": str(exc),
        }
    return total_new


def can_trigger_manual(debounce_minutes: int) -> bool:
    if _last_manual_run is None:
        return True
    return (datetime.now(timezone.utc) - _last_manual_run).total_seconds() / 60 >= debounce_minutes


def mark_manual_triggered() -> None:
    global _last_manual_run
    _last_manual_run = datetime.now(timezone.utc)


async def get_source_stats(session: AsyncSession) -> list[dict]:
    configs = await ensure_source_configs(session)
    counts_result = await session.execute(
        apply_canada_filter(select(Job.source, func.count(Job.id)).where(Job.is_active == True)).group_by(Job.source)  # noqa: E712
    )
    counts = dict(counts_result.all())
    return [
        {
            "source": name,
            "display_name": definition.display_name,
            "enabled": configs[name].enabled,
            "job_count": counts.get(name, 0),
            "credential_status": credential_status(definition),
            "rate_limit": configs[name].rate_limit,
            "last_success": configs[name].last_success,
            "last_error": configs[name].last_error,
        }
        for name, definition in SOURCE_DEFINITIONS.items()
    ]
