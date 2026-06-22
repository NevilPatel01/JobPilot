from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://jobpilot:password@localhost:5432/jobpilot"
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
    public_api_rate_limit_create: str = "10/minute"
    public_api_rate_limit_default: str = "60/minute"
    rate_limit_storage_uri: str = "memory://"
    job_intelligence_enabled: bool = True
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

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def target_province_codes(self) -> list[str]:
        return [code.strip().upper() for code in self.target_provinces.split(",") if code.strip()]


settings = Settings()
