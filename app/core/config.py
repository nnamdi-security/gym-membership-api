from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "FitPro API"
    app_env: str = "developement"
    debug: bool =False


    database_url: str
    redis_url: str

    secret_key: str
    access_token_expire_minutes: int = 60

    daily_job_api_key: str
    webhook_secret: str

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings() 