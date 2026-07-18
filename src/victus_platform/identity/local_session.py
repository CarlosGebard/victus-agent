from __future__ import annotations

from datetime import UTC, datetime, timedelta
import json
import os
from pathlib import Path
from typing import Any

import httpx

TOKEN_ENV_VAR = "VICTUS_API_TOKEN"
BACKEND_API_URL_ENV_VAR = "BACKEND_API_URL"
AUTH_BASE_URL_ENV_VAR = "VICTUS_AUTH_BASE_URL"
OAUTH_CLIENT_ID_ENV_VAR = "VICTUS_OAUTH_CLIENT_ID"
DEFAULT_AUTH_BASE_URL = "http://localhost:8000"
DEFAULT_OAUTH_CLIENT_ID = "victus-cli"
TOKEN_ENDPOINT = "/oauth/token"
SESSION_DIR_NAME = ".victus"
SESSION_FILE_NAME = "session.json"
TOKEN_REFRESH_SKEW_SECONDS = 60


def get_local_token() -> str | None:
    """Return the local Victus API token without logging or raising on malformed state.

    `VICTUS_API_TOKEN` remains a development override. The persisted OAuth session format stores
    `access_token`; the original mock format stored `VICTUS_API_TOKEN`.
    """
    env_token = os.getenv(TOKEN_ENV_VAR)
    if env_token:
        return env_token

    payload = load_local_session()
    if not payload:
        return None

    token = payload.get("access_token") or payload.get(TOKEN_ENV_VAR)
    return token if isinstance(token, str) and token else None


async def get_valid_access_token() -> str | None:
    """Return a usable access token, refreshing the local OAuth session when possible."""
    env_token = os.getenv(TOKEN_ENV_VAR)
    if env_token:
        return env_token

    payload = load_local_session()
    if not payload:
        return None

    token = payload.get("access_token")
    if isinstance(token, str) and token and not _is_expired_or_near_expiry(payload):
        return token

    refresh_token = payload.get("refresh_token")
    if not isinstance(refresh_token, str) or not refresh_token:
        legacy_token = payload.get(TOKEN_ENV_VAR)
        return legacy_token if isinstance(legacy_token, str) and legacy_token else None

    refreshed = await refresh_local_session(refresh_token)
    if not refreshed:
        return None
    refreshed_token = refreshed.get("access_token")
    return refreshed_token if isinstance(refreshed_token, str) and refreshed_token else None


def load_local_session() -> dict[str, Any] | None:
    """Load the local session JSON, returning None for missing or corrupted state."""
    session_file = _session_file_path()
    try:
        raw = session_file.read_text(encoding="utf-8")
        payload = json.loads(raw)
    except (OSError, json.JSONDecodeError):
        return None

    if not isinstance(payload, dict):
        return None
    return payload


def save_local_token(token: str) -> Path:
    """Persist a local Victus API token for the MCP server to relay later."""
    session_file = _session_file_path()
    session_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    session_file.write_text(json.dumps({TOKEN_ENV_VAR: token}, indent=2), encoding="utf-8")
    session_file.chmod(0o600)
    return session_file


def save_oauth_session(token_payload: dict[str, Any]) -> Path:
    """Persist an OAuth token response using the local session format."""
    session = _session_from_token_payload(token_payload)
    return save_local_session(session)


def save_local_session(session: dict[str, Any]) -> Path:
    session_file = _session_file_path()
    session_file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    session_file.write_text(json.dumps(session, indent=2), encoding="utf-8")
    session_file.chmod(0o600)
    return session_file


def delete_local_session() -> bool:
    try:
        _session_file_path().unlink()
    except FileNotFoundError:
        return False
    except OSError:
        return False
    return True


async def refresh_local_session(refresh_token: str) -> dict[str, Any] | None:
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.post(
                _token_url(),
                json={
                    "grant_type": "refresh_token",
                    "client_id": oauth_client_id(),
                    "refresh_token": refresh_token,
                },
            )
        except httpx.HTTPError:
            return None

    if response.status_code != 200:
        return None
    try:
        payload = response.json()
    except ValueError:
        return None
    if not isinstance(payload, dict):
        return None
    save_oauth_session(payload)
    return load_local_session()


def auth_base_url() -> str:
    explicit = os.getenv(AUTH_BASE_URL_ENV_VAR)
    if explicit:
        return explicit.rstrip("/")

    backend_api_url = os.getenv(BACKEND_API_URL_ENV_VAR)
    if backend_api_url:
        value = backend_api_url.rstrip("/")
        if value.endswith("/v1"):
            value = value.removesuffix("/v1")
        return value

    return DEFAULT_AUTH_BASE_URL


def oauth_client_id() -> str:
    return os.getenv(OAUTH_CLIENT_ID_ENV_VAR, DEFAULT_OAUTH_CLIENT_ID)


def _session_file_path() -> Path:
    return Path.home() / SESSION_DIR_NAME / SESSION_FILE_NAME


def _token_url() -> str:
    return f"{auth_base_url()}{TOKEN_ENDPOINT}"


def _session_from_token_payload(payload: dict[str, Any]) -> dict[str, Any]:
    expires_at = payload.get("expires_at")
    if not isinstance(expires_at, str):
        expires_in = payload.get("expires_in", 3600)
        try:
            seconds = int(expires_in)
        except (TypeError, ValueError):
            seconds = 3600
        expires_at = (datetime.now(UTC) + timedelta(seconds=seconds)).isoformat()

    session: dict[str, Any] = {
        "access_token": payload.get("access_token"),
        "refresh_token": payload.get("refresh_token"),
        "expires_at": expires_at,
        "token_type": payload.get("token_type", "Bearer"),
        "scope": payload.get("scope", ""),
    }
    return {key: value for key, value in session.items() if value is not None}


def _is_expired_or_near_expiry(session: dict[str, Any]) -> bool:
    expires_at = session.get("expires_at")
    if not isinstance(expires_at, str) or not expires_at:
        return False
    try:
        expiry = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
    except ValueError:
        return True
    if expiry.tzinfo is None:
        expiry = expiry.replace(tzinfo=UTC)
    return expiry <= datetime.now(UTC) + timedelta(seconds=TOKEN_REFRESH_SKEW_SECONDS)
