from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

from tools.catalog import list_tools
from victus_platform.llm.contracts import LLMClient, LLMRequest
from victus_platform.llm.factory import build_llm_client

DEFAULT_CASES = Path("ops/evals/mcp_intent_cases.json")

SYSTEM_PROMPT = """You route Victus user messages to at most one available function.
Select a function only when its description matches the user's actual intent. If no function applies,
respond with NO_TOOL and do not call a function. The current test user_id is {user_id}. For every
normalized_text argument, copy the user message exactly, character for character; never summarize,
translate, or change its grammatical person. clarification and confirmation are continuation tools:
do not call them unless the message contains enough pending-workflow context."""


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate Victus tool selection through LiteLLM without executing tools."
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument(
        "--model",
        default=os.getenv("INTENT_EVAL_MODEL", "litellm_proxy/gemini-flash-lite"),
    )
    parser.add_argument("--user-id", default="mcp-smoke-user")
    args = parser.parse_args(argv)

    try:
        cases = load_cases(args.cases)
        results = run_cases(
            cases,
            client=build_llm_client(),
            model=args.model,
            user_id=args.user_id,
        )
    except (OSError, ValueError, RuntimeError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False))
        return 2

    passed = sum(bool(result["passed"]) for result in results)
    report = {
        "status": "passed" if passed == len(results) else "failed",
        "model": args.model,
        "selection_only": True,
        "passed": passed,
        "total": len(results),
        "results": results,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed == len(results) else 1


def load_cases(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list) or not data:
        raise ValueError("intent cases must be a non-empty JSON array")
    for case in data:
        if not isinstance(case, dict) or not case.get("id") or not case.get("input"):
            raise ValueError("each intent case requires non-empty id and input fields")
    return data


def run_cases(
    cases: list[dict[str, Any]],
    *,
    client: LLMClient,
    model: str,
    user_id: str,
) -> list[dict[str, Any]]:
    tools = function_tools()
    results = []
    for case in cases:
        response = client.complete(
            LLMRequest(
                operation="eval.mcp_intent_selection",
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT.format(user_id=user_id)},
                    {"role": "user", "content": str(case["input"])},
                ],
                temperature=0,
                tools=tools,
                tool_choice="auto",
                metadata={"case_id": case["id"], "selection_only": True},
            )
        )
        results.append(score_case(case, response.tool_calls, user_id=user_id))
    return results


def function_tools() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": definition.name,
                "description": definition.description,
                "parameters": definition.input_schema,
            },
        }
        for definition in list_tools(exposure="mcp")
    ]


def score_case(
    case: dict[str, Any],
    tool_calls: list[dict[str, Any]],
    *,
    user_id: str,
) -> dict[str, Any]:
    expected_tool = case.get("expected_tool")
    selected_tool = tool_calls[0].get("name") if len(tool_calls) == 1 else None
    arguments = tool_calls[0].get("arguments", {}) if len(tool_calls) == 1 else {}
    reasons = []

    if len(tool_calls) > 1:
        reasons.append("expected at most one tool call")
    if selected_tool != expected_tool:
        reasons.append(f"expected tool {expected_tool!r}, got {selected_tool!r}")
    if selected_tool and selected_tool != "recuperar_perfil" and arguments.get("user_id") != user_id:
        reasons.append("user_id was missing or changed")
    if field := case.get("exact_input_argument"):
        if arguments.get(field) != case["input"]:
            reasons.append(f"{field} did not preserve the exact user input")
    for key, expected in case.get("expected_arguments", {}).items():
        if arguments.get(key) != expected:
            reasons.append(f"argument {key!r} expected {expected!r}, got {arguments.get(key)!r}")

    return {
        "id": case["id"],
        "passed": not reasons,
        "expected_tool": expected_tool,
        "selected_tool": selected_tool,
        "arguments": arguments,
        "reasons": reasons,
    }


if __name__ == "__main__":
    raise SystemExit(main())
