from __future__ import annotations

import json

from agent.nodes.event_capture.policy import decide_with_policy
from agent.nodes.event_capture.prompts import (
    EVENT_CAPTURE_SYSTEM_PROMPT,
    build_event_capture_prompt,
)
from agent.nodes.event_capture.schemas import EventCaptureDecision, EventCaptureInput
from agent.nodes.event_capture.validators import validate_event_capture_decision
from application.ports.llm import LLMClient, LLMRequest


class EventCaptureNode:
    def __init__(self, *, llm_client: LLMClient | None = None, model: str | None = None):
        self.llm_client = llm_client
        self.model = model

    def __call__(self, input: EventCaptureInput) -> EventCaptureDecision:
        return self.run(input)

    def run(self, input: EventCaptureInput) -> EventCaptureDecision:
        decision = self._decide(input)
        return validate_event_capture_decision(decision, input)

    def _decide(self, input: EventCaptureInput) -> EventCaptureDecision:
        if not self.llm_client or not self.model:
            return decide_with_policy(input)

        response = self.llm_client.complete(
            LLMRequest(
                operation="agent.event_capture.decide",
                model=self.model,
                messages=[
                    {"role": "system", "content": EVENT_CAPTURE_SYSTEM_PROMPT},
                    {"role": "user", "content": build_event_capture_prompt(input)},
                ],
                temperature=0,
                max_tokens=700,
                response_format={"type": "json_object"},
                metadata={"node": "event_capture", "user_id": input.user_id},
            )
        )
        return EventCaptureDecision.model_validate(json.loads(response.text))


def event_capture_node(
    *,
    llm_client: LLMClient | None = None,
    model: str | None = None,
) -> EventCaptureNode:
    return EventCaptureNode(llm_client=llm_client, model=model)
