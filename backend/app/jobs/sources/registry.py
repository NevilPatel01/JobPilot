from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.jobs.sources.adzuna import AdzunaSource
from app.jobs.sources.base import CanadianJobSource
from app.jobs.sources.job_bank import JobBankSource
from app.jobs.sources.jsearch import JSearchSource
from app.models.job_intelligence import JobSourceConfig


@dataclass(frozen=True)
class SourceDefinition:
    name: str
    display_name: str
    requires_credentials: bool
    rate_limit: str | None
    adapter: type[CanadianJobSource] | None = None


SOURCE_DEFINITIONS = {
    definition.name: definition
    for definition in (
        SourceDefinition("job_bank", "Job Bank Canada", False, "Conservative public search", JobBankSource),
        SourceDefinition("adzuna", "Adzuna Canada", True, "Provider plan quota", AdzunaSource),
        SourceDefinition("jsearch", "JSearch", True, "RapidAPI plan quota", JSearchSource),
        SourceDefinition("remoteok", "RemoteOK", False, "Public API"),
        SourceDefinition("weworkremotely", "We Work Remotely", False, "Public RSS feeds"),
        SourceDefinition("hackernews", "Hacker News", False, "Algolia public API"),
    )
}


async def ensure_source_configs(session: AsyncSession) -> dict[str, JobSourceConfig]:
    result = await session.execute(select(JobSourceConfig))
    configs = {config.name: config for config in result.scalars().all()}
    for definition in SOURCE_DEFINITIONS.values():
        if definition.name not in configs:
            config = JobSourceConfig(
                name=definition.name,
                enabled=True,
                rate_limit=definition.rate_limit,
                settings_json={
                    "display_name": definition.display_name,
                    "requires_credentials": definition.requires_credentials,
                },
            )
            session.add(config)
            configs[definition.name] = config
    await session.flush()
    return configs


def credential_status(definition: SourceDefinition) -> str:
    if not definition.requires_credentials:
        return "not_required"
    if definition.adapter is None:
        return "missing"
    return definition.adapter().credential_status
