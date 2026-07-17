from __future__ import annotations

import sys
from importlib import import_module

import pytest

from victus_cli.oauth_login import LoginError, LoginResult
from victus_cli import main as cli_main

victus_cli_main_module = import_module("victus_cli.main")


def test_cli_test_runs_pytest(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def run(command: list[str], check: bool) -> CompletedProcess:
        calls.append(command)
        return CompletedProcess(0)

    monkeypatch.setattr(victus_cli_main_module.subprocess, "run", run)
    monkeypatch.setattr(sys, "argv", ["victus", "test", "tests/agent"])

    assert cli_main() == 0
    assert calls == [[sys.executable, "-m", "pytest", "tests/agent"]]


def test_cli_check_stops_when_tests_fail(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def run(command: list[str], check: bool) -> CompletedProcess:
        calls.append(command)
        return CompletedProcess(1)

    monkeypatch.setattr(victus_cli_main_module.subprocess, "run", run)
    monkeypatch.setattr(sys, "argv", ["victus", "check"])

    assert cli_main() == 1
    assert calls == [[sys.executable, "-m", "pytest"]]


def test_cli_db_upgrade_runs_alembic(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def run(command: list[str], check: bool) -> CompletedProcess:
        calls.append(command)
        return CompletedProcess(0)

    monkeypatch.setattr(victus_cli_main_module.subprocess, "run", run)
    monkeypatch.setattr(sys, "argv", ["victus", "db-upgrade"])

    assert cli_main() == 0
    assert calls == [[sys.executable, "-m", "alembic", "-c", "ops/db/alembic.ini", "upgrade", "head"]]


def test_cli_db_current_runs_alembic(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def run(command: list[str], check: bool) -> CompletedProcess:
        calls.append(command)
        return CompletedProcess(0)

    monkeypatch.setattr(victus_cli_main_module.subprocess, "run", run)
    monkeypatch.setattr(sys, "argv", ["victus", "db-current"])

    assert cli_main() == 0
    assert calls == [[sys.executable, "-m", "alembic", "-c", "ops/db/alembic.ini", "current"]]


def test_cli_projection_rebuild_uses_direct_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def rebuild(user_id: str) -> int:
        calls.append(user_id)
        return 0

    monkeypatch.setattr(victus_cli_main_module, "_projections_rebuild", rebuild)
    monkeypatch.setattr(sys, "argv", ["victus", "projections-rebuild", "user-1"])

    assert cli_main() == 0
    assert calls == ["user-1"]


def test_cli_mcp_call_rejects_invalid_json(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.setattr(sys, "argv", ["victus", "mcp-call", "event_capture", "not-json"])

    assert cli_main() == 2
    assert "invalid arguments JSON" in capsys.readouterr().err


def test_cli_login_runs_browser_oauth(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    def login() -> LoginResult:
        return LoginResult(session_path="/tmp/session.json")

    from victus_cli import oauth_login

    monkeypatch.setattr(oauth_login, "run_browser_login", login)
    monkeypatch.setattr(sys, "argv", ["victus", "login"])

    assert cli_main() == 0

    output = capsys.readouterr().out
    assert "Victus session saved" in output


def test_cli_login_reports_oauth_errors(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    def login() -> LoginResult:
        raise LoginError("login failed")

    from victus_cli import oauth_login

    monkeypatch.setattr(oauth_login, "run_browser_login", login)
    monkeypatch.setattr(sys, "argv", ["victus", "login"])

    assert cli_main() == 2
    assert "login failed" in capsys.readouterr().err


def test_cli_logout_removes_session(monkeypatch: pytest.MonkeyPatch, tmp_path, capsys) -> None:
    session_dir = tmp_path / ".victus"
    session_dir.mkdir()
    (session_dir / "session.json").write_text("{}", encoding="utf-8")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(sys, "argv", ["victus", "logout"])

    assert cli_main() == 0
    assert not (session_dir / "session.json").exists()
    assert "Victus session removed" in capsys.readouterr().out


def test_cli_self_harm_response_prints_json(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.setattr(
        sys,
        "argv",
        ["victus", "self-harm-response", "I am going to hurt myself"],
    )

    assert cli_main() == 0

    output = capsys.readouterr().out
    assert '"decision": "route_to_safety_triage"' in output
    assert '"mode": "safety_triage"' in output


def test_cli_safety_check_prints_llama_guard_router_response_and_safety(
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    from infrastructure.llm.hugging_face_endpoint import HuggingFaceRouterResult
    from infrastructure.llm import hugging_face_endpoint

    class StubRouterClient:
        def __init__(self, *, base_url: str, token: str | None = None) -> None:
            assert base_url == "https://router.huggingface.co/v1"
            assert token == "test-token"

        def complete_guard(self, *, model: str, user_text: str):
            assert model == "meta-llama/Llama-Guard-4-12B:together"
            assert user_text == "I am going to hurt myself"
            return HuggingFaceRouterResult(
                text="unsafe\nS11",
                model=model,
                raw={"usage": {"total_tokens": 12}},
            )

    monkeypatch.setenv("HF_TOKEN", "test-token")
    monkeypatch.delenv("HUGGING_FACE_ROUTER_BASE_URL", raising=False)
    monkeypatch.setattr(hugging_face_endpoint, "HuggingFaceRouterClient", StubRouterClient)
    monkeypatch.setattr(sys, "argv", ["victus", "safety-check", "I am going to hurt myself"])

    assert cli_main() == 0

    output = capsys.readouterr().out
    assert '"model": "meta-llama/Llama-Guard-4-12B:together"' in output
    assert '"source": "hugging_face_router"' in output
    assert '"raw_response": "unsafe\\nS11"' in output
    assert '"categories": [' in output
    assert '"self_harm"' in output
    assert '"total_tokens": 12' in output


def test_cli_safety_check_uses_custom_hugging_face_router_base_url(
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    from infrastructure.llm.hugging_face_endpoint import HuggingFaceRouterResult
    from infrastructure.llm import hugging_face_endpoint

    class StubRouterClient:
        def __init__(self, *, base_url: str, token: str | None = None) -> None:
            assert base_url == "https://router.test/v1"
            assert token == "test-token"

        def complete_guard(self, *, model: str, user_text: str):
            assert user_text == "How to make a bomb?"
            return HuggingFaceRouterResult(
                text="unsafe\nS9",
                model=model,
                raw={"id": "chatcmpl-test"},
            )

    monkeypatch.setenv("HUGGING_FACE_ROUTER_BASE_URL", "https://router.test/v1")
    monkeypatch.setenv("HF_TOKEN", "test-token")
    monkeypatch.setattr(hugging_face_endpoint, "HuggingFaceRouterClient", StubRouterClient)
    monkeypatch.setattr(sys, "argv", ["victus", "safety-check", "How to make a bomb?"])

    assert cli_main() == 0

    output = capsys.readouterr().out
    assert '"raw_response": "unsafe\\nS9"' in output
    assert '"indiscriminate_weapons"' in output


class CompletedProcess:
    def __init__(self, returncode: int) -> None:
        self.returncode = returncode
