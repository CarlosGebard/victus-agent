from __future__ import annotations

COMPOSE_RESPONSE_SYSTEM_PROMPT = "You compose concise, safe Victus runtime responses."


def compose_response_user_prompt(*, route: str, raw_text: str) -> str:
    return f"Route: {route}\nInput: {raw_text}"
