from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


TaskStatus = Literal["open", "waiting_user", "completed", "blocked"]
PendingKind = Literal["question", "confirmation", "choice", "proposal"]


class ActiveTask(ContractModel):
    task_name: str
    task_status: TaskStatus
    next_expected_step: str | None = None


class PendingInteractionState(ContractModel):
    conversation_id: str
    user_id: str
    pending_kind: PendingKind
    assistant_prompt: str
    expected_user_response: str
    resume_graph: str | None = None
    resume_node: str | None = None
    created_at: str
    updated_at: str


class ConversationStateSummary(ContractModel):
    conversation_id: str
    user_id: str
    summary_version: str = "session-context-v1"
    user_current_goal: str = ""
    current_topic: str = ""
    stable_decisions: list[str] = Field(default_factory=list)
    recent_decisions: list[str] = Field(default_factory=list)
    active_task: ActiveTask | None = None
    pending_interaction: PendingInteractionState | None = None
    relevant_context: list[str] = Field(default_factory=list)
    last_tool_summary: str | None = None
    unresolved_questions: list[str] = Field(default_factory=list)
    should_inject_next_turn: bool = True
    updated_at: str


class BootstrapContext(ContractModel):
    conversation_id: str | None = None
    summary: ConversationStateSummary | None = None
    pending_interaction: PendingInteractionState | None = None
    recent_user_messages: list[str] = Field(default_factory=list)
    last_tool_summary: str | None = None
    routing_query: str
