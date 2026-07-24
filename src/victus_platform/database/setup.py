from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from alembic import command
from alembic.config import Config
from sqlalchemy import text

from victus_platform.database.engine import build_engine, database_url

SCHEMA_SETUP_LOCK_ID = 8_624_021
REPOSITORY_ROOT = Path(__file__).resolve().parents[3]


@contextmanager
def schema_setup_lock(url: str | None = None) -> Iterator[str]:
    resolved_url = url or database_url()
    engine = build_engine(resolved_url)
    try:
        with engine.connect() as connection:
            connection.execute(
                text("SELECT pg_advisory_lock(:lock_id)"),
                {"lock_id": SCHEMA_SETUP_LOCK_ID},
            )
            try:
                yield resolved_url
            finally:
                connection.execute(
                    text("SELECT pg_advisory_unlock(:lock_id)"),
                    {"lock_id": SCHEMA_SETUP_LOCK_ID},
                )
    finally:
        engine.dispose()


def upgrade_database_schema(url: str | None = None) -> None:
    resolved_url = url or database_url()
    config = Config(str(REPOSITORY_ROOT / "ops/db/alembic.ini"))
    config.set_main_option("script_location", str(REPOSITORY_ROOT / "ops/db/migrations"))
    config.set_main_option("sqlalchemy.url", resolved_url)
    command.upgrade(config, "head")
