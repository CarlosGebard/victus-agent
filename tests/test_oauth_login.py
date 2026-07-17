from __future__ import annotations

import base64
from hashlib import sha256
from urllib.parse import parse_qs, urlparse

import pytest

from victus_cli import oauth_login


def test_code_challenge_uses_pkce_s256() -> None:
    verifier = "test-verifier"
    expected = base64.urlsafe_b64encode(sha256(verifier.encode("ascii")).digest())
    expected_text = expected.decode("ascii").rstrip("=")

    assert oauth_login._code_challenge(verifier) == expected_text


def test_authorization_url_uses_backend_and_pkce_params(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BACKEND_API_URL", "http://localhost:8000")
    url = oauth_login._authorization_url(
        redirect_uri="http://127.0.0.1:49152/callback",
        state="state-1",
        code_challenge="challenge-1",
    )

    parsed = urlparse(url)
    params = parse_qs(parsed.query)

    assert f"{parsed.scheme}://{parsed.netloc}{parsed.path}" == (
        "http://localhost:8000/oauth/authorize"
    )
    assert params["client_id"] == ["victus-cli"]
    assert params["redirect_uri"] == ["http://127.0.0.1:49152/callback"]
    assert params["state"] == ["state-1"]
    assert params["code_challenge"] == ["challenge-1"]
    assert params["code_challenge_method"] == ["S256"]


def test_exchange_code_saves_token_response(monkeypatch: pytest.MonkeyPatch, tmp_path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("BACKEND_API_URL", "http://localhost:8000")
    calls = []

    def post(url: str, *, json: dict[str, str], timeout: float) -> FakeResponse:
        calls.append((url, json, timeout))
        return FakeResponse(
            200,
            {
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "expires_in": 3600,
                "token_type": "Bearer",
                "scope": "openid profile",
            },
        )

    monkeypatch.setattr(oauth_login.httpx, "post", post)

    payload = oauth_login._exchange_code(
        code="code-1",
        redirect_uri="http://127.0.0.1:49152/callback",
        code_verifier="verifier-1",
    )

    assert payload["access_token"] == "access-token"
    assert calls == [
        (
            "http://localhost:8000/oauth/token",
            {
                "grant_type": "authorization_code",
                "client_id": "victus-cli",
                "code": "code-1",
                "redirect_uri": "http://127.0.0.1:49152/callback",
                "code_verifier": "verifier-1",
            },
            10.0,
        )
    ]


def test_callback_html_matches_victus_success_state() -> None:
    html = oauth_login._callback_html(success=True)

    assert "Victus login completo" in html
    assert "Cuenta privada" in html
    assert "Tu CLI ya quedo conectada" in html
    assert "#030504" in html
    assert "#0f9d58" in html


def test_callback_html_matches_victus_error_state() -> None:
    html = oauth_login._callback_html(success=False)

    assert "Victus login incompleto" in html
    assert "No recibimos el codigo de autorizacion" in html
    assert "Reintentar" in html


class FakeResponse:
    def __init__(self, status_code: int, payload: object) -> None:
        self.status_code = status_code
        self._payload = payload

    def json(self) -> object:
        return self._payload
