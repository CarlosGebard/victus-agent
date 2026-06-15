from __future__ import annotations

import os

from sqlalchemy import Engine, create_engine


def database_url() -> str:
    value = os.getenv("DATABASE_URL")
    if not value:
        raise RuntimeError("DATABASE_URL is required for database operations")
    return value


def build_engine(url: str | None = None) -> Engine:
    return create_engine(url or database_url(), future=True)
