from __future__ import annotations

import base64
from dataclasses import dataclass
from hashlib import sha256
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from queue import Queue, Empty
import secrets
from threading import Thread
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse
import webbrowser

import httpx

from victus_mcp.utils.auth import auth_base_url, oauth_client_id, save_oauth_session

AUTHORIZE_ENDPOINT = "/oauth/authorize"
TOKEN_ENDPOINT = "/oauth/token"
DEFAULT_SCOPE = "openid profile email offline_access"
LOGIN_TIMEOUT_SECONDS = 180


@dataclass(frozen=True)
class LoginResult:
    session_path: str


@dataclass(frozen=True)
class CallbackResult:
    code: str | None
    state: str | None
    error: str | None = None


class LoginError(RuntimeError):
    pass


def run_browser_login() -> LoginResult:
    verifier = _code_verifier()
    challenge = _code_challenge(verifier)
    state = secrets.token_urlsafe(32)

    queue: Queue[CallbackResult] = Queue(maxsize=1)
    server = _CallbackServer(("127.0.0.1", 0), _callback_handler(queue))
    host, port = server.server_address
    redirect_uri = f"http://{host}:{port}/callback"
    url = _authorization_url(
        redirect_uri=redirect_uri,
        state=state,
        code_challenge=challenge,
    )

    thread = Thread(target=server.handle_request, daemon=True)
    thread.start()

    opened = webbrowser.open(url, new=2)
    if not opened:
        print(f"Open this URL to log in to Victus:\n{url}")

    try:
        callback = queue.get(timeout=LOGIN_TIMEOUT_SECONDS)
    except Empty as exc:
        raise LoginError("login timed out waiting for browser callback") from exc
    finally:
        server.server_close()
        thread.join(timeout=1)

    if callback.error:
        raise LoginError(f"login failed: {callback.error}")
    if callback.state != state:
        raise LoginError("login failed: invalid OAuth state")
    if not callback.code:
        raise LoginError("login failed: missing authorization code")

    token_payload = _exchange_code(
        code=callback.code,
        redirect_uri=redirect_uri,
        code_verifier=verifier,
    )
    session_path = save_oauth_session(token_payload)
    return LoginResult(session_path=str(session_path))


def _authorization_url(*, redirect_uri: str, state: str, code_challenge: str) -> str:
    query = urlencode(
        {
            "response_type": "code",
            "client_id": oauth_client_id(),
            "redirect_uri": redirect_uri,
            "scope": DEFAULT_SCOPE,
            "state": state,
            "code_challenge": code_challenge,
            "code_challenge_method": "S256",
        }
    )
    return f"{auth_base_url()}{AUTHORIZE_ENDPOINT}?{query}"


def _callback_html(*, success: bool) -> str:
    title = "Victus login completo" if success else "Victus login incompleto"
    eyebrow = "Sesion conectada" if success else "Autorizacion pendiente"
    message = (
        "Tu CLI ya quedo conectada. Puedes cerrar esta pestana y volver a la terminal."
        if success
        else "No recibimos el codigo de autorizacion. Vuelve a la terminal e intenta iniciar sesion otra vez."
    )
    status = "Listo" if success else "Reintentar"
    status_class = "status success" if success else "status warning"
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title}</title>
  <style>
    :root {{
      color-scheme: dark;
      --font-sans: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      --color-bg-canvas: #030504;
      --color-bg-surface: #080c09;
      --color-bg-subtle: #0d120f;
      --color-border-subtle: rgba(255, 255, 255, 0.07);
      --color-border-default: rgba(255, 255, 255, 0.11);
      --color-text-primary: #f2f5f3;
      --color-text-secondary: #a9b2ac;
      --color-text-muted: #747f78;
      --color-accent: #0f9d58;
      --color-accent-subtle: rgba(15, 157, 88, 0.12);
      --color-accent-border: rgba(15, 157, 88, 0.32);
      --color-warning: #d7a646;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      min-height: 100dvh;
      margin: 0;
      display: grid;
      place-items: center;
      padding: 24px;
      background:
        radial-gradient(circle at 50% 22%, rgba(15, 157, 88, 0.12) 0 18rem, transparent 36rem),
        var(--color-bg-canvas);
      color: var(--color-text-primary);
      font-family: var(--font-sans);
    }}
    main {{
      width: min(100%, 560px);
      border: 1px solid var(--color-border-subtle);
      border-radius: 12px;
      background: rgba(8, 12, 9, 0.9);
      padding: clamp(28px, 6vw, 48px);
    }}
    .brand {{ display: flex; align-items: center; gap: 12px; margin-bottom: 28px; }}
    .mark {{
      display: grid;
      width: 38px;
      height: 38px;
      place-items: center;
      border: 1px solid var(--color-accent-border);
      border-radius: 8px;
      background: var(--color-accent-subtle);
      color: var(--color-accent);
      font-weight: 900;
    }}
    .brand-copy {{ display: flex; flex-direction: column; gap: 3px; }}
    .brand-copy strong {{ font-size: 18px; letter-spacing: 0; }}
    .brand-copy span {{ color: var(--color-text-muted); font-size: 12px; }}
    .eyebrow {{
      color: var(--color-accent);
      font-size: 12px;
      font-weight: 800;
      letter-spacing: 0;
      text-transform: uppercase;
    }}
    h1 {{
      max-width: 480px;
      margin: 10px 0 0;
      font-size: clamp(34px, 8vw, 52px);
      font-weight: 900;
      letter-spacing: 0;
      line-height: 1;
      text-wrap: balance;
    }}
    p {{
      max-width: 470px;
      margin: 16px 0 0;
      color: var(--color-text-secondary);
      font-size: 15px;
      line-height: 1.65;
    }}
    .status-row {{ display: flex; flex-wrap: wrap; gap: 8px; margin-top: 24px; }}
    .status {{
      display: inline-flex;
      align-items: center;
      gap: 8px;
      border: 1px solid var(--color-border-default);
      border-radius: 8px;
      padding: 8px 10px;
      color: var(--color-text-secondary);
      font-size: 13px;
      font-weight: 700;
    }}
    .status::before {{
      content: "";
      width: 8px;
      height: 8px;
      border-radius: 999px;
      background: var(--color-accent);
      box-shadow: 0 0 0 4px var(--color-accent-subtle);
    }}
    .status.warning::before {{
      background: var(--color-warning);
      box-shadow: 0 0 0 4px rgba(215, 166, 70, 0.14);
    }}
  </style>
</head>
<body>
  <main>
    <div class="brand" aria-label="Victus">
      <div class="mark">V</div>
      <div class="brand-copy">
        <strong>Victus</strong>
        <span>Cuenta privada</span>
      </div>
    </div>
    <div class="eyebrow">{eyebrow}</div>
    <h1>{title}</h1>
    <p>{message}</p>
    <div class="status-row"><span class="{status_class}">{status}</span></div>
  </main>
</body>
</html>"""


def _exchange_code(*, code: str, redirect_uri: str, code_verifier: str) -> dict[str, Any]:
    try:
        response = httpx.post(
            f"{auth_base_url()}{TOKEN_ENDPOINT}",
            json={
                "grant_type": "authorization_code",
                "client_id": oauth_client_id(),
                "code": code,
                "redirect_uri": redirect_uri,
                "code_verifier": code_verifier,
            },
            timeout=10.0,
        )
    except httpx.HTTPError as exc:
        raise LoginError("login failed: unable to reach OAuth token endpoint") from exc

    if response.status_code != 200:
        raise LoginError(f"login failed: token endpoint returned {response.status_code}")
    try:
        payload = response.json()
    except ValueError as exc:
        raise LoginError("login failed: invalid token response") from exc
    if not isinstance(payload, dict) or not payload.get("access_token"):
        raise LoginError("login failed: token response did not include access_token")
    return payload


def _callback_handler(queue: Queue[CallbackResult]):
    class Handler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            parsed = urlparse(self.path)
            params = parse_qs(parsed.query)
            result = CallbackResult(
                code=_first(params.get("code")),
                state=_first(params.get("state")),
                error=_first(params.get("error")),
            )
            try:
                queue.put_nowait(result)
            except Exception:
                pass
            self._send_html(200, success=bool(result.code))

        def log_message(self, format: str, *args: object) -> None:
            return

        def _send_html(self, status: int, *, success: bool) -> None:
            html = _callback_html(success=success).encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(html)))
            self.end_headers()
            self.wfile.write(html)

    return Handler


class _CallbackServer(ThreadingHTTPServer):
    allow_reuse_address = True


def _code_verifier() -> str:
    return secrets.token_urlsafe(64)


def _code_challenge(verifier: str) -> str:
    digest = sha256(verifier.encode("ascii")).digest()
    return base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")


def _first(values: list[str] | None) -> str | None:
    if not values:
        return None
    return values[0]
