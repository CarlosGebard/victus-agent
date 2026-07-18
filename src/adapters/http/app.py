from __future__ import annotations

import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from langgraph.types import Command
from pydantic import ValidationError
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from adapters.http.auth import BackendIdentityResolver, IdentityResolver
from adapters.langgraph.contracts import ChatInterrupt, ChatRequest, ChatResponse
from adapters.langgraph.graph import build_graph
from adapters.langgraph.persistence import postgres_graph_resources
from adapters.langgraph.state import GRAPH_VERSION
from bootstrap.runtime import projection_repository_scope
from victus_platform.database.engine import database_url
from victus_platform.llm.factory import build_llm_client

DEFAULT_HOST = "0.0.0.0"
DEFAULT_PORT = 8766


def create_app(*, graph: Any | None = None, identity_resolver: IdentityResolver | None = None) -> Starlette:
    resolver = identity_resolver or BackendIdentityResolver()

    @asynccontextmanager
    async def lifespan(app: Starlette) -> AsyncIterator[None]:
        if graph is not None:
            app.state.graph = graph
            app.state.store = None
            yield
            return
        async with postgres_graph_resources(database_url()) as resources:
            client = build_llm_client()
            app.state.graph = build_graph(
                llm_client=client,
                checkpointer=resources.checkpointer,
                store=resources.store,
                projection_scope=projection_repository_scope,
            )
            app.state.store = resources.store
            yield

    async def health(request: Request) -> JSONResponse:
        configured = bool(os.getenv("DATABASE_URL") and os.getenv("LITELLM_PROXY_API_BASE"))
        ready = configured or graph is not None
        if configured and graph is None:
            try:
                config = {
                    "configurable": {
                        "thread_id": "__readiness__",
                        "user_id": "__readiness__",
                    }
                }
                await request.app.state.graph.aget_state(config)
                await request.app.state.store.asearch(("system", "readiness"), limit=1)
            except Exception:
                ready = False
        return JSONResponse(
            {"status": "ok" if ready else "not_ready", "service": "victus-agent-chat"},
            status_code=200 if ready else 503,
        )

    async def chat(request: Request) -> JSONResponse:
        token = _bearer_token(request)
        if token is None:
            return JSONResponse({"error": "missing bearer token"}, status_code=401)
        try:
            user_id = await resolver.resolve(token)
        except RuntimeError as exc:
            return JSONResponse({"error": str(exc)}, status_code=503)
        if not user_id:
            return JSONResponse({"error": "invalid bearer token"}, status_code=401)
        try:
            payload = ChatRequest.model_validate(await request.json())
        except (ValidationError, ValueError) as exc:
            return JSONResponse({"error": "invalid request", "details": str(exc)}, status_code=422)

        config = {"configurable": {"thread_id": payload.conversation_id, "user_id": user_id}}
        snapshot = await request.app.state.graph.aget_state(config)
        values = snapshot.values or {}
        owner = values.get("request", {}).get("user_id")
        if owner and owner != user_id:
            return JSONResponse({"error": "conversation is owned by another user"}, status_code=403)
        if values.get("graph_version") not in (None, GRAPH_VERSION):
            return JSONResponse({"error": "conversation graph version is incompatible"}, status_code=409)

        if payload.resume is not None:
            if not values or not snapshot.next:
                return JSONResponse({"error": "conversation is not awaiting a response"}, status_code=409)
            graph_input: Any = Command(resume=payload.resume.value)
        else:
            graph_input = {
                "request": {
                    "request_id": payload.request_id,
                    "user_id": user_id,
                    "raw_text": payload.message,
                    "conversation_id": payload.conversation_id,
                    "locale": payload.locale,
                    "timezone": payload.timezone,
                }
            }

        try:
            result = await request.app.state.graph.ainvoke(graph_input, config=config)
        except Exception:
            return JSONResponse({"error": "agent execution failed"}, status_code=503)
        response = _chat_response(payload.conversation_id, result)
        return JSONResponse(response.model_dump(mode="json", exclude_none=True))

    return Starlette(
        debug=False,
        lifespan=lifespan,
        routes=[Route("/health", health), Route("/chat", chat, methods=["POST"])],
    )


def _bearer_token(request: Request) -> str | None:
    authorization = request.headers.get("authorization", "")
    scheme, _, token = authorization.partition(" ")
    return token if scheme.lower() == "bearer" and token else None


def _chat_response(conversation_id: str, state: dict[str, Any]) -> ChatResponse:
    interrupts = state.get("__interrupt__") or []
    if interrupts:
        item = interrupts[0]
        value = item.value if hasattr(item, "value") else item.get("value", {})
        interrupt_id = item.id if hasattr(item, "id") else str(item.get("id", ""))
        value = value if isinstance(value, dict) else {}
        interrupt = ChatInterrupt(
            id=interrupt_id,
            kind=str(value.get("kind") or "input"),
            question=str(value.get("question") or "Se necesita una respuesta."),
            details={key: val for key, val in value.items() if key not in {"kind", "question"}},
        )
        return ChatResponse(
            conversation_id=conversation_id,
            status="needs_user_response",
            message=interrupt.question,
            interrupt=interrupt,
        )
    response = state.get("response", {})
    tool = state.get("tool_context", {}).get("last_tool_result")
    mode = response.get("mode", "error")
    status = "blocked" if mode == "blocked" else "error" if mode == "error" else "completed"
    events = list((tool or {}).get("events_emitted", []))
    trace_id = ((tool or {}).get("meta") or {}).get("trace_id")
    return ChatResponse(
        conversation_id=conversation_id,
        status=status,
        message=str(response.get("user_message") or ""),
        tool=tool,
        events=events,
        trace_id=trace_id,
    )


def main() -> None:
    import uvicorn

    uvicorn.run(
        create_app(),
        host=os.getenv("VICTUS_CHAT_HTTP_HOST", DEFAULT_HOST),
        port=int(os.getenv("VICTUS_CHAT_HTTP_PORT", str(DEFAULT_PORT))),
    )


if __name__ == "__main__":
    main()
