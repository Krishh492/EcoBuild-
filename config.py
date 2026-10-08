"""
EcoBuild Configuration
Supports SQLite for local development;
PostgreSQL-ready via DATABASE_URL environment variable.
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent


class Config:
    # ── Security ──────────────────────────────────────────────────────────────
    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "change-me-in-production"
    )

    WTF_CSRF_ENABLED = True

    # ── Database ──────────────────────────────────────────────────────────────
    DATABASE_URL = os.environ.get("DATABASE_URL")

    # Fix legacy database URI prefixes on Render
    if DATABASE_URL:
        if DATABASE_URL.startswith("postgres://"):
            DATABASE_URL = DATABASE_URL.replace(
                "postgres://",
                "postgresql://",
                1
            )

        # Use psycopg 3 explicitly
        elif (
            DATABASE_URL.startswith("postgresql://")
            and not DATABASE_URL.startswith("postgresql+psycopg://")
        ):
            DATABASE_URL = DATABASE_URL.replace(
                "postgresql://",
                "postgresql+psycopg://",
                1
            )

    SQLALCHEMY_DATABASE_URI = (
        DATABASE_URL
        or f"sqlite:///{BASE_DIR / 'ecobuild.db'}"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ── Session ───────────────────────────────────────────────────────────────
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    # ── Debug ─────────────────────────────────────────────────────────────────
    DEBUG = False
    TESTING = False


class DevelopmentConfig(Config):
    DEBUG = True
    SESSION_COOKIE_SECURE = False


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Enforces HTTPS on Render


# ── Configuration Map ─────────────────────────────────────────────────────────
config_map = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "default": ProductionConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "production")
    return config_map.get(env, ProductionConfig)