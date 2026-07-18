from __future__ import annotations

import os
from typing import Protocol

import httpx


class IdentityResolver(Protocol):
    async def resolve(self, token: str) -> str | None: ...


class BackendIdentityResolver:
    async def resolve(self, token: str) -> str | None:
        base_url = os.getenv("BACKEND_API_URL")
        if not base_url:
            raise RuntimeError("BACKEND_API_URL is required for chat authentication")
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{base_url.rstrip('/')}/me",
                headers={"Authorization": f"Bearer {token}"},
            )
        if response.status_code != 200:
            return None
        payload = response.json()
        if not isinstance(payload, dict):
            return None
        for key in ("user_id", "id", "sub"):
            value = payload.get(key)
            if isinstance(value, str) and value:
                return value
        return None
