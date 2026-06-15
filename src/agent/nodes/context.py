from __future__ import annotations

import os
from typing import Protocol

from agent.nodes.runtime import _merge
from agent.prompts.translation import GROQ_TRANSLATION_SYSTEM_PROMPT, groq_translation_user_prompt
from agent.state import VictusGraphState
from application.ports.llm import LLMClient, LLMRequest
from domain.session_context.models import BootstrapContext

DEFAULT_GROQ_TRANSLATION_MODEL = "groq/llama-3.1-8b-instant"


class SessionContextReader(Protocol):
    def get_latest_summary(self, conversation_id: str): ...

    def get_pending_interaction(self, conversation_id: str): ...


def context_bootstrap(
    repository: SessionContextReader | None = None,
    *,
    llm_client: LLMClient | None = None,
):
    if llm_client:
        return _context_bootstrap_async(repository=repository, llm_client=llm_client)
    return _context_bootstrap_sync(repository=repository)


def _context_bootstrap_sync(repository: SessionContextReader | None = None):
    def node(state: VictusGraphState) -> VictusGraphState:
        request = dict(state.get("request", {}))
        original_text = str(request.get("original_text", ""))
        working_text = str(request.get("working_text") or original_text)
        conversation_id = request.get("conversation_id")
        summary = None
        pending = None

        if repository and conversation_id:
            summary = repository.get_latest_summary(conversation_id)
            pending = repository.get_pending_interaction(conversation_id)

        working_text = _build_working_text(working_text, pending)
        request["working_text"] = working_text
        bootstrap = BootstrapContext(
            conversation_id=conversation_id,
            summary=summary,
            pending_interaction=pending,
            routing_query=working_text,
        )
        session_context = dict(state.get("session_context", {}))
        if conversation_id:
            session_context["conversation_id"] = conversation_id
        if summary:
            session_context["summary"] = summary
        if pending:
            session_context["pending_interaction"] = pending
        session_context["bootstrap"] = bootstrap

        return _merge(
            state,
            request=request,
            session_context=session_context,
            node_name="context_bootstrap",
        )

    return node


def _context_bootstrap_async(
    *,
    repository: SessionContextReader | None = None,
    llm_client: LLMClient,
):
    async def node(state: VictusGraphState) -> VictusGraphState:
        state = await _translate_normalized_text(state, llm_client)
        return _context_bootstrap_sync(repository)(state)

    return node


async def _translate_normalized_text(
    state: VictusGraphState,
    llm_client: LLMClient,
) -> VictusGraphState:
    request = dict(state.get("request", {}))
    working_text = str(request.get("working_text") or "")
    if not working_text:
        return state

    response = await llm_client.acomplete(
        LLMRequest(
            operation="agent.context_bootstrap.translate_normalized_text",
            model=os.getenv("GROQ_TRANSLATION_MODEL", DEFAULT_GROQ_TRANSLATION_MODEL),
            messages=[
                {
                    "role": "system",
                    "content": GROQ_TRANSLATION_SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": groq_translation_user_prompt(working_text),
                },
            ],
            temperature=0,
            max_tokens=40,
            metadata={"source": "request.working_text", "target_language": "en"},
        )
    )
    translated = response.text.strip()
    if translated:
        request["working_text"] = translated
    return _merge(
        state,
        request=request,
        node_name="context_bootstrap.translate_working_text",
        transform={"step": "translate", "input": working_text, "output": translated},
    )


def _build_working_text(working_text: str, pending: object | None) -> str:
    if not pending:
        return working_text
    assistant_prompt = getattr(pending, "assistant_prompt", "")
    expected = getattr(pending, "expected_user_response", "")
    resume_graph = getattr(pending, "resume_graph", None)
    resume_node = getattr(pending, "resume_node", None)
    resume_target = ".".join(part for part in [resume_graph, resume_node] if part)
    return (
        "Pending interaction context:\n"
        f"Assistant prompt: {assistant_prompt}\n"
        f"Expected user response: {expected}\n"
        f"Resume target: {resume_target or 'unspecified'}\n"
        f"Current user message: {working_text}"
    )
