from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def normalize_database_url(url: str) -> str:
    """Accept Neon-style postgresql:// URLs and ensure asyncpg driver prefix."""
    if not url:
        return url
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://") :]
    if url.startswith("postgresql://") and "+asyncpg" not in url.split("://", 1)[0]:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # asyncpg uses ssl=require, not sslmode=require (Neon default)
    url = url.replace("sslmode=require", "ssl=require")
    url = url.replace("sslmode=verify-full", "ssl=require")
    url = url.replace("sslmode=prefer", "ssl=prefer")
    return url


def sync_database_url(url: str) -> str:
    """psycopg2 URL for Alembic migrations (no asyncpg driver)."""
    url = normalize_database_url(url)
    url = url.replace("postgresql+asyncpg://", "postgresql://")
    url = url.replace("ssl=require", "sslmode=require")
    url = url.replace("ssl=prefer", "sslmode=prefer")
    return url


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://jobpilot:password@localhost:5432/jobpilot"
    neon_connection_string: str = ""
    secret_key: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 10080
    google_client_id: str = ""
    github_client_id: str = ""
    vapid_private_key: str = ""
    vapid_public_key: str = ""
    vapid_claims_email: str = "admin@jobpilot.local"
    scraper_debounce_minutes: int = 10
    match_score_threshold: int = 40
    allowed_origins: str = "http://localhost:3000"
    auth_disabled: bool = False
    tectonic_path: str = ""
    application_uploads_dir: str = "data/application_resumes"
    public_api_rate_limit_create: str = "10/minute"
    public_api_rate_limit_default: str = "60/minute"
    rate_limit_storage_uri: str = "memory://"
    job_intelligence_enabled: bool = True
    feature_candidate_intelligence: bool = False
    target_provinces: str = "AB,BC,ON,SK"
    adzuna_app_id: str = ""
    adzuna_app_key: str = ""
    adzuna_country: str = "ca"
    rapidapi_key: str = ""
    jsearch_host: str = "jsearch.p.rapidapi.com"
    job_bank_api_key: str = ""
    scraper_timezone: str = "America/Toronto"
    scraper_morning_hour: int = 8
    scraper_evening_hour: int = 18
    scraper_evening_enabled: bool = True
    scraper_dry_run: bool = False
    scraper_max_queries_per_source: int = 12
    scraper_max_pages: int = 1
    scraper_fetch_descriptions: bool = True
    fit_score_low_max: int = 40
    fit_score_stretch_max: int = 59
    fit_score_reviewed_max: int = 74
    fit_score_recommended_max: int = 84
    gmail_forward_enabled: bool = False
    gmail_inbound_domain: str = ""
    gmail_oauth_enabled: bool = False
    gmail_client_id: str = ""
    gmail_client_secret: str = ""
    job_catalog_retention_days: int = 180
    inbox_auto_archive_days: int = 45
    raw_payload_retention_days: int = 45
    followup_first_business_days: int = 5
    followup_second_business_days: int = 10
    cron_secret: str = ""
    disable_apscheduler: bool = False

    @field_validator("database_url", mode="before")
    @classmethod
    def _normalize_database_url_field(cls, value: object) -> object:
        if isinstance(value, str):
            return normalize_database_url(value)
        return value

    @property
    def resolved_database_url(self) -> str:
        raw = (self.neon_connection_string or self.database_url).strip()
        return normalize_database_url(raw)

    @property
    def resolved_sync_database_url(self) -> str:
        return sync_database_url(self.resolved_database_url)

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def target_province_codes(self) -> list[str]:
        return [code.strip().upper() for code in self.target_provinces.split(",") if code.strip()]


settings = Settings()
