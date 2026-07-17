from __future__ import annotations

import asyncio
import json
from typing import Any

from application.tools import execute_tool_async, list_tools


def build_server():
    import mcp.types as types
    from mcp.server.lowlevel import Server

    server = Server("victus-agent")

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return [
            types.Tool(
                name=definition.name,
                description=definition.description,
                inputSchema=definition.input_schema,
            )
            for definition in list_tools(visible_only=True)
        ]

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[types.ContentBlock]:
        result = await execute_tool_async(name, arguments)
        return [
            types.TextContent(
                type="text",
                text=json.dumps(result.model_dump(mode="json"), ensure_ascii=False),
            )
        ]

    return server


async def run_stdio() -> None:
    from mcp.server.lowlevel import NotificationOptions
    from mcp.server.models import InitializationOptions
    from mcp.server.stdio import stdio_server

    server = build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="victus-agent",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


def main() -> None:
    asyncio.run(run_stdio())


if __name__ == "__main__":
    main()
