from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4


def new_event_id() -> str:
    return str(uuid4())


def new_prefixed_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex}"


def now_iso() -> str:
    return datetime.now(UTC).isoformat()


def clean_leading_article(value: str | None) -> str:
    if not value:
        return "unknown"
    for article in ("el ", "la ", "los ", "las "):
        if value.startswith(article):
            return value.removeprefix(article).strip() or "unknown"
    return value
