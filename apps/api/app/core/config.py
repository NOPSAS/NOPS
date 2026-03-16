"""
ByggSjekk – Application configuration.
Reads settings from environment variables or a .env file.
"""

from __future__ import annotations

from typing import List

from pydantic import AnyHttpUrl, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # --------------- Application ---------------
    APP_NAME: str = "ByggSjekk"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"

    # --------------- Database ------------------
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/byggsjekk"

    # --------------- Redis / ARQ ---------------
    REDIS_URL: str = "redis://localhost:6379/0"

    # --------------- Security ------------------
    SECRET_KEY: str = "CHANGE_ME_in_production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # --------------- MinIO / S3 ----------------
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET: str = "byggsjekk"
    MINIO_USE_SSL: bool = False

    # --------------- LLM -----------------------
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-6"
    LLM_PROVIDER: str = "anthropic"  # "openai" | "anthropic"

    # --------------- Geodata / DOK-analyse -----
    GEODATA_TOKEN: str = ""           # Geodata AS API-token for DOK-analyse

    # --------------- Norkart / Arealplaner.no --
    AREALPLANER_API_KEY: str = ""     # Norkart API-nøkkel
    AREALPLANER_BASE_URL: str = "https://www.arealplaner.no/api"

    # --------------- SMTP ----------------------
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""

    # --------------- nops.no ------------------
    NOPS_BASE_URL: str = "https://nops.no"

    # --------------- Stripe --------------------
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    # Prisplan-IDer fra Stripe Dashboard
    STRIPE_PRICE_STARTER_MONTHLY: str = ""   # ~499 kr/mnd
    STRIPE_PRICE_STARTER_YEARLY: str = ""    # ~4490 kr/år
    STRIPE_PRICE_PRO_MONTHLY: str = ""       # ~999 kr/mnd
    STRIPE_PRICE_PRO_YEARLY: str = ""        # ~8990 kr/år

    # --------------- E-post (utvidet) ----------
    EMAIL_FROM: str = "nops@nops.no"
    EMAIL_FROM_NAME: str = "nops.no"

    # --------------- CORS ----------------------
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
    ]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: str | List[str]) -> List[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v


settings = Settings()


def get_settings() -> Settings:
    return settings
