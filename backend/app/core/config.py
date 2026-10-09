from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения."""

    database_url: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/Meal_planner"
    secret_key: str = "development-secret-change-me"
    openrouter_api_key: str | None = None
    openrouter_model: str = "apodex/apodex-1.1-mini:free"
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    openrouter_timeout_seconds: int = 120
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    debug: bool = False
    model_config = SettingsConfigDict(env_file=ENV_FILE, env_file_encoding="utf-8", extra="ignore")


settings = Settings()
