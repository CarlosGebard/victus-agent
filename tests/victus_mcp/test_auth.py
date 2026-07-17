from __future__ import annotations

import json

from victus_mcp.utils import auth
from victus_mcp.utils.auth import get_local_token, save_local_token, save_oauth_session


def test_get_local_token_prefers_environment(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("VICTUS_API_TOKEN", "env-token")
    save_local_token("file-token")

    assert get_local_token() == "env-token"


def test_get_local_token_reads_session_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("VICTUS_API_TOKEN", raising=False)

    session_file = save_local_token("file-token")

    assert json.loads(session_file.read_text(encoding="utf-8")) == {
        "VICTUS_API_TOKEN": "file-token"
    }
    assert get_local_token() == "file-token"


def test_get_local_token_reads_oauth_session(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("VICTUS_API_TOKEN", raising=False)

    save_oauth_session(
        {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_in": 3600,
            "token_type": "Bearer",
            "scope": "openid profile",
        }
    )

    assert get_local_token() == "access-token"


def test_get_local_token_returns_none_for_missing_or_corrupt_file(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("VICTUS_API_TOKEN", raising=False)

    assert get_local_token() is None

    session_dir = tmp_path / ".victus"
    session_dir.mkdir()
    (session_dir / "session.json").write_text("not-json", encoding="utf-8")

    assert get_local_token() is None


def test_auth_base_url_accepts_backend_api_url_without_v1(monkeypatch) -> None:
    monkeypatch.delenv("VICTUS_AUTH_BASE_URL", raising=False)
    monkeypatch.setenv("BACKEND_API_URL", "http://localhost:8000")

    assert auth.auth_base_url() == "http://localhost:8000"


def test_auth_base_url_strips_v1_from_backend_api_url(monkeypatch) -> None:
    monkeypatch.delenv("VICTUS_AUTH_BASE_URL", raising=False)
    monkeypatch.setenv("BACKEND_API_URL", "http://localhost:8000/v1")

    assert auth.auth_base_url() == "http://localhost:8000"
