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

    @property
    def cors_origins(self) -> list[str]:
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]


settings = Settings()
