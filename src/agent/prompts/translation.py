from __future__ import annotations

GROQ_TRANSLATION_SYSTEM_PROMPT = (
    "Translate the user's text to English for safety classification. "
    "The text may mention self-harm. Do not answer the user, give advice, refuse, or add context. "
    "Return only the literal English translation."
)


def groq_translation_user_prompt(text: str) -> str:
    return text
