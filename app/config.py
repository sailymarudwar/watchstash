from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    anthropic_api_key: str
    tmdb_api_key: str
    omdb_api_key: str
    region: str = "US"
    claude_model: str = "claude-haiku-5-5"
    http_timeout_seconds: float = 10.0
    database_url: str = "sqlite:///watchstash.db"
    access_codes: str = ""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        """Hosts give postgres:// URLs, but SQLAlchemy needs the driver named."""
        for prefix in ("postgres://", "postgresql://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        return value

    @property
    def users(self) -> dict[str, str]:
        """Maps each access code to a person's name."""
        pairs = (p.split(":", 1) for p in self.access_codes.split(",") if ":" in p)
        return {code.strip(): name.strip() for name, code in pairs}


@lru_cache
def get_settings() -> Settings:
    return Settings()