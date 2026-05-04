from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "sweet-neighbors-club"

    DATABASE_URL: str
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str | None = None
    CELERY_RESULT_BACKEND: str | None = None
    CELERY_RESULT_EXPIRES_SECONDS: int = 3600

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
    CIAN_USER_AGENT: str | None = None
    SCRAPING_BEAT_ENABLED: bool = True
    SCRAPING_INTERVAL_MINUTES: int = 10
    SCRAPER_STALE_MISSES_THRESHOLD: int = 3
    NOTIFICATIONS_MATCHER_BATCH_SIZE: int = 100

    SMTP_HOST: str | None = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM: str | None = None
    SMTP_USE_TLS: bool = True

    WEB_PUSH_VAPID_PUBLIC_KEY: str | None = None
    WEB_PUSH_VAPID_PRIVATE_KEY: str | None = None
    WEB_PUSH_VAPID_CLAIMS_SUBJECT: str | None = None

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
