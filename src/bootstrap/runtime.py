from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Iterator

from tools.runtime import ToolRuntime
from tools.contracts import ToolMeta, ToolResult, ToolSafety, ToolServices
from victus_platform.identity.profile_gateway import BackendProfileGateway
from victus_platform.safety.rules import SafetyPrecheck, SafetyPrecheckInput
from victus_platform.telemetry import new_trace_id


@contextmanager
def event_store_scope() -> Iterator[object | None]:
    if not os.getenv("DATABASE_URL"):
        yield None
        return

    from victus_platform.database.engine import build_engine
    from victus_platform.repositories.events import PostgresEventStore

    engine = build_engine()
    with engine.begin() as connection:
        yield PostgresEventStore(connection)


def build_runtime() -> ToolRuntime:
    return ToolRuntime(
        event_store_scope=event_store_scope,
        services=ToolServices({"profile_gateway": BackendProfileGateway()}),
        trace_id_factory=new_trace_id,
        precheck=safety_precheck,
    )


def safety_precheck(input_data, context) -> ToolResult | None:
    text = getattr(input_data, "normalized_text", None)
    if not isinstance(text, str) or not text:
        return None
    result = SafetyPrecheck().check(
        SafetyPrecheckInput(original_text=text, working_text=text)
    )
    if result.decision == "allow":
        return None
    return ToolResult(
        status="blocked",
        safety=ToolSafety(status="blocked", reasons=result.reason_codes),
        meta=ToolMeta(trace_id=context.trace_id),
    )
