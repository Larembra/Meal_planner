from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения из переменных окружения."""

    database_url: str = "sqlite+aiosqlite:///./meal_planner.db"
    secret_key: str = "development-secret-change-me"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    debug: bool = False
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
