from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    supabase_url: str = ""
    supabase_service_role_key: str = ""
    supabase_db_url: str = ""

    google_api_key: str = ""
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    mp_access_token: str = ""
    mp_webhook_secret: str = ""

    admin_emails: str = ""
    web_origin: str = ""

    @property
    def cors_origins(self) -> list[str]:
        origins = ["http://localhost:3000"]
        if self.web_origin:
            origins.append(self.web_origin)
        return origins

    @field_validator("supabase_url")
    @classmethod
    def normalize_supabase_url(cls, value: str) -> str:
        """Accept either the bare project URL or a full REST endpoint URL, and
        always return the bare project URL (e.g. https://xxx.supabase.co)."""
        return value.removesuffix("/rest/v1/").removesuffix("/rest/v1").removesuffix("/")

    @property
    def admin_email_list(self) -> list[str]:
        return [email.strip().lower() for email in self.admin_emails.split(",") if email.strip()]


settings = Settings()
