from __future__ import annotations

from adapters.langgraph.state import VictusGraphState
from adapters.langgraph.context import _merge
from domain.shared.text import normalize_text
from tools.contracts import ToolContext, ToolInvocation
from tools.runtime import ToolRuntime


def tool_node(name: str, runtime: ToolRuntime):
    def node(state: VictusGraphState) -> VictusGraphState:
        request = dict(state.get("request", {}))
        original_text = str(
            request.get("original_text")
            or request.get("raw_text")
            or request.get("working_text")
            or ""
        )
        working_text = str(request.get("working_text") or normalize_text(original_text))
        user_id = str(request.get("user_id") or "local-user")
        result = runtime.invoke(
            ToolInvocation(
                name=name,
                arguments={"user_id": user_id, "normalized_text": working_text},
                context=ToolContext(source="langgraph"),
            )
        )
        request.pop("raw_text", None)
        request.update(original_text=original_text, working_text=working_text)
        tool_context = dict(state.get("tool_context", {}))
        tool_context["last_tool_result"] = {
            "tool_name": name,
            **result.model_dump(mode="json"),
        }
        data = result.data if isinstance(result.data, dict) else {}
        return _merge(
            state,
            request=request,
            tool_context=tool_context,
            intent={
                "primary_intent": name,
                "confidence": 1.0,
                "target_node": name,
                "subintents": [],
                "rationale": data.get("reason", ""),
            },
            node_name=name,
        )

    return node
