from __future__ import annotations

import inspect
from collections.abc import Callable
from contextlib import nullcontext
from typing import Any
from uuid import uuid4

from domain.events.refs import ToolEventRef
from tools.catalog import get_tool
from tools.contracts import (
    ToolContext,
    ToolError,
    ToolExecution,
    ToolInvocation,
    ToolMeta,
    ToolResult,
    ToolServices,
    ToolStatus,
)


class ToolRuntimeError(ValueError):
    pass


class ToolRuntime:
    def __init__(
        self,
        event_store_scope: Callable[[], Any] | None = None,
        authorizer: Callable[[Any, ToolContext], bool] | None = None,
        precheck: Callable[[Any, ToolContext], ToolResult | None] | None = None,
        services: ToolServices | None = None,
        trace_id_factory: Callable[[], str] | None = None,
    ) -> None:
        self._event_store_scope = event_store_scope or (lambda: nullcontext(None))
        self._authorizer = authorizer
        self._precheck = precheck
        self._services = services or ToolServices()
        self._trace_id_factory = trace_id_factory or (lambda: str(uuid4()))

    def invoke(self, invocation: ToolInvocation) -> ToolResult:
        try:
            definition, input_data, context = self._prepare(invocation)
            if result := self._run_precheck(input_data, context):
                return result
            execution = definition.implementation(input_data, context, self._services)
            if inspect.isawaitable(execution):
                raise ToolRuntimeError(f"tool requires async invocation: {definition.name}")
            return self._persist(execution, context)
        except ValueError as exc:
            return self._error_result(invocation, "invalid_invocation", str(exc), "rejected")
        except Exception:
            return self._error_result(
                invocation, "execution_error", "tool execution failed", "error"
            )

    async def invoke_async(self, invocation: ToolInvocation) -> ToolResult:
        try:
            definition, input_data, context = self._prepare(invocation)
            if result := self._run_precheck(input_data, context):
                return result
            execution = definition.implementation(input_data, context, self._services)
            if inspect.isawaitable(execution):
                execution = await execution
            return self._persist(execution, context)
        except ValueError as exc:
            return self._error_result(invocation, "invalid_invocation", str(exc), "rejected")
        except Exception:
            return self._error_result(
                invocation, "execution_error", "tool execution failed", "error"
            )

    def _prepare(self, invocation: ToolInvocation):
        definition = get_tool(invocation.name)
        if invocation.context.source not in definition.exposures:
            raise ToolRuntimeError(
                f"tool {definition.name} is not exposed to {invocation.context.source}"
            )
        if definition.requires_identity and not invocation.context.identity.authenticated:
            raise ToolRuntimeError(f"tool requires identity: {definition.name}")
        context = invocation.context.model_copy(
            update={"trace_id": invocation.context.trace_id or self._trace_id_factory()}
        )
        input_data = definition.input_model.model_validate(invocation.arguments)
        input_user_id = getattr(input_data, "user_id", None)
        if (
            context.identity.subject
            and input_user_id is not None
            and input_user_id != context.identity.subject
        ):
            raise ToolRuntimeError("invocation identity does not match user_id")
        if self._authorizer and not self._authorizer(definition, context):
            raise ToolRuntimeError(f"tool is not authorized: {definition.name}")
        return definition, input_data, context

    def _run_precheck(self, input_data: Any, context: ToolContext) -> ToolResult | None:
        return self._precheck(input_data, context) if self._precheck else None

    def _persist(self, execution: ToolExecution, context: ToolContext) -> ToolResult:
        refs: list[ToolEventRef] = []
        if execution.events:
            with self._event_store_scope() as store:
                if store is not None:
                    for index, event in enumerate(execution.events):
                        if context.idempotency_key:
                            key = context.idempotency_key
                            if len(execution.events) > 1:
                                key = f"{key}:{index}"
                            event = event.model_copy(update={"idempotency_key": key})
                        metadata = event.metadata.model_copy(update={"trace_id": context.trace_id})
                        event = event.model_copy(
                            update={"correlation_id": context.trace_id, "metadata": metadata}
                        )
                        appended = store.append(event)
                        refs.append(
                            ToolEventRef(
                                event_id=appended.event_id,
                                event_type=appended.event_type,
                                seq=appended.event_seq,
                            )
                        )
        meta = execution.result.meta.model_copy(update={"trace_id": context.trace_id})
        return execution.result.model_copy(update={"events_emitted": refs, "meta": meta})

    def _error_result(
        self, invocation: ToolInvocation, code: str, message: str, status: ToolStatus
    ) -> ToolResult:
        trace_id = invocation.context.trace_id or self._trace_id_factory()
        return ToolResult(
            status=status,
            error=ToolError(code=code, message=message),
            meta=ToolMeta(trace_id=trace_id),
        )
