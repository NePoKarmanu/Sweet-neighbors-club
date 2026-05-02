from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "sweet-neighbors-club"

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None

    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    CIAN_SEARCH_URL: str = (
        "https://voronezh.cian.ru/cat.php?currency=2&deal_type=rent&engine_version=2"
        "&maxprice=20000&minprice=10000&offer_type=flat&region=4713&room2=1&type=4"
    )
    CIAN_REQUEST_TIMEOUT_SECONDS: int = 20
    CIAN_COOKIE: str | None = None
    SCRAPING_BEAT_ENABLED: bool = True
    SCRAPING_INTERVAL_MINUTES: int = 10

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
