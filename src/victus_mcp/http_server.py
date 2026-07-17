from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Mount, Route

from victus_mcp.server import build_server

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8765
MCP_PATH = "/mcp"


def create_app() -> Starlette:
    mcp_server = build_server()
    session_manager = StreamableHTTPSessionManager(
        app=mcp_server,
        json_response=True,
        stateless=True,
    )

    @asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        async with session_manager.run():
            yield

    async def health(request: Request) -> JSONResponse:
        return JSONResponse(
            {
                "status": "ok",
                "service": "victus-agent-mcp-http",
                "transport": "streamable_http",
            }
        )

    return Starlette(
        debug=False,
        lifespan=lifespan,
        routes=[
            Route("/health", health, methods=["GET"]),
            Mount(MCP_PATH, app=session_manager.handle_request),
        ],
    )


def main() -> None:
    import uvicorn

    host = os.getenv("VICTUS_MCP_HTTP_HOST", DEFAULT_HOST)
    port = int(os.getenv("VICTUS_MCP_HTTP_PORT", str(DEFAULT_PORT)))
    uvicorn.run(create_app(), host=host, port=port)


if __name__ == "__main__":
    main()
