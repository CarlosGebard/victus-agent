from __future__ import annotations

import asyncio

from adapters.langgraph.runtime.persistence import setup_postgres_graph_storage
from victus_platform.database.setup import schema_setup_lock, upgrade_database_schema


async def prepare_agent_storage() -> None:
    await asyncio.to_thread(_prepare_storage, include_langgraph=True)


async def prepare_mcp_storage() -> None:
    await asyncio.to_thread(_prepare_storage, include_langgraph=False)


def _prepare_storage(*, include_langgraph: bool) -> None:
    with schema_setup_lock() as database_url:
        upgrade_database_schema(database_url)
        if include_langgraph:
            asyncio.run(setup_postgres_graph_storage(database_url))
