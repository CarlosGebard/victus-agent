from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from typing import Any

from adapters.langgraph.capabilities.contracts import MemoryDocument
from adapters.langgraph.engine.state import VictusGraphState
from adapters.langgraph.runtime.context import _merge

MEMORY_LIMIT = 8
_DOMAIN_TERMS = re.compile(
    r"\b(alerg|intoler|restric|diabet|enfermed|medic|peso|altura|com[ií]|comida|"
    r"s[ií]ntoma|dolor|meta|plan|calor[ií]a|prote[ií]na)\w*\b",
    re.IGNORECASE,
)


def memory_namespace(user_id: str, kind: str) -> tuple[str, ...]:
    return ("users", user_id, "agent_memory", kind)


def recall_long_term_memory(store: Any | None):
    async def node(state: VictusGraphState) -> VictusGraphState:
        user_id = str(state.get("request", {}).get("user_id") or "")
        recalled: list[dict[str, Any]] = []
        if store is not None and user_id:
            for kind in ("procedural", "semantic"):
                items = await store.asearch(memory_namespace(user_id, kind), limit=MEMORY_LIMIT)
                recalled.extend(dict(item.value) for item in items[:MEMORY_LIMIT])
        memory = dict(state.get("memory", {}))
        memory["recalled"] = recalled[:MEMORY_LIMIT]
        return _merge(state, memory=memory, node_name="recall_long_term_memory")

    return node


def update_long_term_memory(store: Any | None):
    async def node(state: VictusGraphState) -> VictusGraphState:
        if store is None:
            return _merge(state, node_name="update_long_term_memory")
        request = state.get("request", {})
        user_id = str(request.get("user_id") or "")
        text = str(request.get("original_text") or "").strip()
        if not user_id or not text:
            return _merge(state, node_name="update_long_term_memory")

        forget = re.match(r"(?i)^\s*(?:olvida|forget)\s+(?:que\s+)?(.+)$", text)
        remember = re.match(r"(?i)^\s*(?:recuerda|remember)\s+(?:que\s+)?(.+)$", text)
        if forget:
            content = forget.group(1).strip()
            for kind in ("procedural", "semantic"):
                await store.adelete(memory_namespace(user_id, kind), _memory_key(content))
        elif remember:
            content = remember.group(1).strip()
            if _allowed_memory(content):
                kind = "procedural" if _is_procedural(content) else "semantic"
                now = datetime.now(UTC)
                document = MemoryDocument(
                    key=_memory_key(content),
                    kind=kind,
                    content=content,
                    source_thread=str(request.get("conversation_id") or ""),
                    source_turn=str(request.get("request_id") or ""),
                    created_at=now,
                    updated_at=now,
                    confidence=1,
                    explicit_user=True,
                )
                await store.aput(
                    memory_namespace(user_id, kind),
                    document.key,
                    document.model_dump(mode="json"),
                    index=False,
                )
        return _merge(state, node_name="update_long_term_memory")

    return node


def _memory_key(content: str) -> str:
    normalized = " ".join(content.lower().split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:24]


def _allowed_memory(content: str) -> bool:
    lowered = content.lower()
    if len(content) > 500 or _DOMAIN_TERMS.search(content):
        return False
    return not any(term in lowered for term in ("password", "contraseña", "token", "secret", "api key"))


def _is_procedural(content: str) -> bool:
    lowered = content.lower()
    return any(term in lowered for term in ("respuesta", "idioma", "breve", "detalle", "tono"))
