from __future__ import annotations

import os

import httpx

from tools.profile.contract import ProfileGatewayResponse
from victus_platform.identity.local_session import get_valid_access_token

DEFAULT_BACKEND_API_URL = "http://localhost:8000/v1"


class BackendProfileGateway:
    async def fetch(self) -> ProfileGatewayResponse:
        token = await get_valid_access_token()
        if not token:
            return ProfileGatewayResponse(status_code=0, error="missing_identity")
        url = f"{os.getenv('BACKEND_API_URL', DEFAULT_BACKEND_API_URL).rstrip('/')}/me"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    url, headers={"Authorization": f"Bearer {token}"}
                )
        except httpx.HTTPError:
            return ProfileGatewayResponse(status_code=0, error="unreachable")
        try:
            payload = response.json()
        except ValueError:
            payload = None
        return ProfileGatewayResponse(status_code=response.status_code, payload=payload)
