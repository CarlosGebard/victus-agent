from __future__ import annotations

from contextlib import AsyncExitStack, asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator

from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
from langgraph.store.postgres.aio import AsyncPostgresStore


def langgraph_dsn(database_url: str) -> str:
    if database_url.startswith("postgresql+psycopg://"):
        return "postgresql://" + database_url.removeprefix("postgresql+psycopg://")
    if database_url.startswith("postgresql+psycopg2://"):
        return "postgresql://" + database_url.removeprefix("postgresql+psycopg2://")
    return database_url


@dataclass(frozen=True)
class PostgresGraphResources:
    checkpointer: AsyncPostgresSaver
    store: AsyncPostgresStore


@asynccontextmanager
async def postgres_graph_resources(database_url: str) -> AsyncIterator[PostgresGraphResources]:
    dsn = langgraph_dsn(database_url)
    async with AsyncExitStack() as stack:
        checkpointer = await stack.enter_async_context(
            AsyncPostgresSaver.from_conn_string(dsn)
        )
        store = await stack.enter_async_context(AsyncPostgresStore.from_conn_string(dsn))
        yield PostgresGraphResources(checkpointer=checkpointer, store=store)


async def setup_postgres_graph_storage(database_url: str) -> None:
    async with postgres_graph_resources(database_url) as resources:
        await resources.checkpointer.setup()
        await resources.store.setup()
