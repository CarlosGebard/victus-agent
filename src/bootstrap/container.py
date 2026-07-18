from __future__ import annotations

from dataclasses import dataclass

from bootstrap.runtime import build_runtime
from tools.runtime import ToolRuntime


@dataclass(frozen=True)
class Container:
    tool_runtime: ToolRuntime


def build_container() -> Container:
    return Container(tool_runtime=build_runtime())
