from __future__ import annotations

import json

from agent.nodes.profile_update.policy import decide_with_policy
from agent.nodes.profile_update.prompts import (
    PROFILE_UPDATE_SYSTEM_PROMPT,
    build_profile_update_prompt,
)
from agent.nodes.profile_update.schemas import ProfileUpdateDecision, ProfileUpdateInput
from agent.nodes.profile_update.validators import validate_profile_update_decision
from application.ports.llm import LLMClient, LLMRequest


class ProfileUpdateNode:
    def __init__(self, *, llm_client: LLMClient | None = None, model: str | None = None):
        self.llm_client = llm_client
        self.model = model

    def __call__(self, input: ProfileUpdateInput) -> ProfileUpdateDecision:
        return self.run(input)

    def run(self, input: ProfileUpdateInput) -> ProfileUpdateDecision:
        decision = self._decide(input)
        return validate_profile_update_decision(decision, input)

    def _decide(self, input: ProfileUpdateInput) -> ProfileUpdateDecision:
        if not self.llm_client or not self.model:
            return decide_with_policy(input)

        response = self.llm_client.complete(
            LLMRequest(
                operation="agent.profile_update.decide",
                model=self.model,
                messages=[
                    {"role": "system", "content": PROFILE_UPDATE_SYSTEM_PROMPT},
                    {"role": "user", "content": build_profile_update_prompt(input)},
                ],
                temperature=0,
                max_tokens=500,
                response_format={"type": "json_object"},
                metadata={"node": "profile_update", "user_id": input.user_id},
            )
        )
        return ProfileUpdateDecision.model_validate(json.loads(response.text))


def profile_update_node(
    *,
    llm_client: LLMClient | None = None,
    model: str | None = None,
) -> ProfileUpdateNode:
    return ProfileUpdateNode(llm_client=llm_client, model=model)
