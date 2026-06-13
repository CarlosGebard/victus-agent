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


class CompletedProcess:
    def __init__(self, returncode: int) -> None:
        self.returncode = returncode
