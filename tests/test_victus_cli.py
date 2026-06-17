from __future__ import annotations

import sys
from importlib import import_module

import pytest

from victus_cli import main as cli_main

victus_cli_main_module = import_module("victus_cli.main")


def test_cli_test_runs_pytest(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def run(command: list[str], check: bool) -> CompletedProcess:
        calls.append(command)
        return CompletedProcess(0)

    monkeypatch.setattr(victus_cli_main_module.subprocess, "run", run)
    monkeypatch.setattr(sys, "argv", ["victus", "test", "tests/routing"])

    assert cli_main() == 0
    assert calls == [[sys.executable, "-m", "pytest", "tests/routing"]]


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
    assert calls == [[sys.executable, "-m", "alembic", "upgrade", "head"]]


def test_cli_db_current_runs_alembic(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[list[str]] = []

    def run(command: list[str], check: bool) -> CompletedProcess:
        calls.append(command)
        return CompletedProcess(0)

    monkeypatch.setattr(victus_cli_main_module.subprocess, "run", run)
    monkeypatch.setattr(sys, "argv", ["victus", "db-current"])

    assert cli_main() == 0
    assert calls == [[sys.executable, "-m", "alembic", "current"]]


def test_cli_projection_rebuild_uses_direct_handler(monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list[str] = []

    def rebuild(user_id: str) -> int:
        calls.append(user_id)
        return 0

    monkeypatch.setattr(victus_cli_main_module, "_projections_rebuild", rebuild)
    monkeypatch.setattr(sys, "argv", ["victus", "projections-rebuild", "user-1"])

    assert cli_main() == 0
    assert calls == ["user-1"]


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


def test_cli_safety_check_prints_model_prompt_raw_response_and_safety(
    monkeypatch: pytest.MonkeyPatch,
    capsys,
) -> None:
    from infrastructure.llm.local_llama_guard import LocalLlamaGuardResult
    from infrastructure.llm import local_llama_guard

    class StubLLMClient:
        def __init__(self, model_name: str) -> None:
            assert model_name == "meta-llama/Llama-Guard-3-1B"

        def complete(self, prompt: str, *, max_new_tokens: int):
            assert "User message:\nI am going to hurt myself" in prompt
            assert max_new_tokens == 64
            return LocalLlamaGuardResult(
                text="unsafe\nS11",
                prompt=prompt,
                raw={"total_tokens": 5},
            )

    monkeypatch.setattr(local_llama_guard, "LocalLlamaGuardClient", StubLLMClient)
    monkeypatch.setattr(sys, "argv", ["victus", "safety-check", "I am going to hurt myself"])

    assert cli_main() == 0

    output = capsys.readouterr().out
    assert '"model": "meta-llama/Llama-Guard-3-1B"' in output
    assert '"raw_response": "unsafe\\nS11"' in output
    assert '"categories": [' in output
    assert '"self_harm"' in output
    assert '"total_tokens": 5' in output


class CompletedProcess:
    def __init__(self, returncode: int) -> None:
        self.returncode = returncode
