from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv


def load_env_file(env_path: Path | None = None) -> None:
    if env_path is None:
        env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(dotenv_path=env_path, override=False)


def get_database_url() -> str:
    load_env_file()

    database_url = os.getenv("DATABASE_URL")
    if database_url:
        return database_url

    db_user = os.getenv("DB_USER", "")
    db_password = os.getenv("DB_PASSWORD", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_port = os.getenv("DB_PORT", "5432")
    db_name = os.getenv("DB_NAME", "")

    if not db_user or not db_password or not db_name:
        raise RuntimeError("Database credentials are not configured in .env")

    return (
        f"postgresql+psycopg://{quote_plus(db_user)}:{quote_plus(db_password)}"
        f"@{db_host}:{db_port}/{db_name}"
    )


def get_jwt_secret_key() -> str:
    load_env_file()

    secret_key = os.getenv("JWT_SECRET_KEY", "")
    if not secret_key:
        raise RuntimeError("JWT_SECRET_KEY is not configured in .env")
    return secret_key


def get_jwt_algorithm() -> str:
    load_env_file()
    return os.getenv("JWT_ALGORITHM", "HS256")


def get_access_token_expire_minutes() -> int:
    load_env_file()
    return int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
