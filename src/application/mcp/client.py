from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MCPClientConfig:
    command: str = "uv"
    args: list[str] = field(default_factory=lambda: ["run", "victus-mcp"])
    env: dict[str, str] = field(default_factory=dict)


class VictusMCPClient:
    def __init__(self, config: MCPClientConfig | None = None) -> None:
        self.config = config or MCPClientConfig()

    async def list_tools(self) -> list[dict[str, Any]]:
        async with self._session() as session:
            response = await session.list_tools()
            return [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema,
                }
                for tool in response.tools
            ]

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        async with self._session() as session:
            result = await session.call_tool(name, arguments=arguments)
            if not result.content:
                return {"status": "error", "data": None, "warnings": ["empty MCP tool result"]}
            text = getattr(result.content[0], "text", "")
            return json.loads(text)

    def _server_params(self):
        from mcp import StdioServerParameters

        env = {**os.environ, **self.config.env} if self.config.env else None
        return StdioServerParameters(command=self.config.command, args=self.config.args, env=env)

    def _session(self):
        return _MCPClientSession(self._server_params())


class _MCPClientSession:
    def __init__(self, server_params: Any) -> None:
        self.server_params = server_params
        self._transport = None
        self._client_session = None

    async def __aenter__(self):
        from mcp import ClientSession
        from mcp.client.stdio import stdio_client

        self._transport = stdio_client(self.server_params)
        read, write = await self._transport.__aenter__()
        self._client_session = ClientSession(read, write)
        session = await self._client_session.__aenter__()
        await session.initialize()
        return session

    async def __aexit__(self, exc_type, exc, tb):
        if self._client_session is not None:
            await self._client_session.__aexit__(exc_type, exc, tb)
        if self._transport is not None:
            await self._transport.__aexit__(exc_type, exc, tb)
