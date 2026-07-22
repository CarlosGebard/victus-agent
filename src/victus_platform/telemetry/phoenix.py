from __future__ import annotations

import os
from contextlib import contextmanager, nullcontext
from typing import Any, Iterator


def initialize_phoenix() -> Any | None:
    if not _environment_flag("PHOENIX_TRACING_ENABLED"):
        return None
    try:
        from phoenix.otel import register
    except ImportError as exc:
        raise RuntimeError(
            "Phoenix tracing is enabled but the 'phoenix' optional dependencies are not installed"
        ) from exc

    return register(auto_instrument=True, batch=True, verbose=False)


def shutdown_phoenix(provider: Any | None) -> None:
    if provider is not None:
        provider.shutdown()


def phoenix_context(
    *,
    session_id: str,
    user_id: str,
    metadata: dict[str, Any] | None = None,
):
    if not _environment_flag("PHOENIX_TRACING_ENABLED"):
        return nullcontext()
    try:
        from phoenix.otel import using_attributes
    except ImportError as exc:
        raise RuntimeError(
            "Phoenix tracing is enabled but the 'phoenix' optional dependencies are not installed"
        ) from exc
    return using_attributes(session_id=session_id, user_id=user_id, metadata=metadata)


@contextmanager
def trace_llm_call(request: Any) -> Iterator[Any | None]:
    if not _environment_flag("PHOENIX_TRACING_ENABLED"):
        yield None
        return
    try:
        from opentelemetry import trace
        from phoenix.otel import OpenInferenceSpanKindValues, SpanAttributes
    except ImportError as exc:
        raise RuntimeError(
            "Phoenix tracing is enabled but the 'phoenix' optional dependencies are not installed"
        ) from exc

    tracer = trace.get_tracer("victus-agent.llm")
    with tracer.start_as_current_span(str(request.operation)) as span:
        span.set_attribute(
            SpanAttributes.OPENINFERENCE_SPAN_KIND,
            OpenInferenceSpanKindValues.LLM.value,
        )
        span.set_attribute(SpanAttributes.LLM_MODEL_NAME, str(request.model))
        span.set_attribute("victus.llm.operation", str(request.operation))
        for key, value in request.metadata.items():
            if _safe_attribute(key, value):
                span.set_attribute(f"victus.metadata.{key}", value)
        yield span


def record_llm_usage(span: Any | None, usage: dict[str, Any]) -> None:
    if span is None:
        return
    from phoenix.otel import SpanAttributes

    counts = (
        ("prompt_tokens", SpanAttributes.LLM_TOKEN_COUNT_PROMPT),
        ("completion_tokens", SpanAttributes.LLM_TOKEN_COUNT_COMPLETION),
        ("total_tokens", SpanAttributes.LLM_TOKEN_COUNT_TOTAL),
    )
    for source, attribute in counts:
        value = usage.get(source)
        if isinstance(value, int):
            span.set_attribute(attribute, value)


def _safe_attribute(key: str, value: Any) -> bool:
    normalized = str(key).lower().replace("-", "_")
    if any(part in normalized for part in ("api_key", "authorization", "password", "secret", "token")):
        return False
    return isinstance(value, (bool, int, float, str))


def _environment_flag(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in {"1", "true", "yes", "on"}
