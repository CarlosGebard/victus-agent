from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

import httpx

from ops.scripts.mcp_intent_eval import (
    DEFAULT_CASES,
    SYSTEM_PROMPT,
    function_tools,
    load_cases,
    score_case,
)
from victus_platform.llm.contracts import LLMClient, LLMRequest
from victus_platform.llm.factory import build_llm_client
from victus_platform.telemetry.phoenix import initialize_phoenix, shutdown_phoenix

DEFAULT_DATASET = "victus-mcp-intent"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run Victus tool-selection cases as a Phoenix experiment."
    )
    parser.add_argument("--cases", type=Path, default=DEFAULT_CASES)
    parser.add_argument(
        "--model",
        default=os.getenv("INTENT_EVAL_MODEL", "litellm_proxy/gemini-flash-lite"),
    )
    parser.add_argument("--user-id", default="mcp-smoke-user")
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--dry-run", type=int, default=0)
    args = parser.parse_args(argv)

    telemetry = None
    try:
        from phoenix.client import Client
        from phoenix.client.experiments import run_experiment

        cases = load_cases(args.cases)
        phoenix = Client()
        dataset = phoenix.datasets.create_dataset(
            name=args.dataset,
            examples=dataset_examples(cases),
            dataset_description="Victus deterministic MCP intent-selection contract cases.",
        )
        telemetry = initialize_phoenix()
        experiment = run_experiment(
            dataset=dataset,
            task=build_task(client=build_llm_client(), model=args.model, user_id=args.user_id),
            evaluators=[build_contract_evaluator(user_id=args.user_id)],
            experiment_name=f"intent-selection:{args.model}",
            experiment_metadata={
                "model": args.model,
                "selection_only": True,
                "case_count": len(cases),
            },
            dry_run=args.dry_run or False,
            client=phoenix,
        )
    except (ImportError, OSError, RuntimeError, ValueError, httpx.HTTPError) as exc:
        print(json.dumps({"status": "error", "message": str(exc)}, ensure_ascii=False))
        return 2
    finally:
        shutdown_phoenix(telemetry)

    passed = all(evaluation_passed(item) for item in experiment["evaluation_runs"])
    report = {
        "status": "passed" if passed else "failed",
        "experiment_id": experiment["experiment_id"],
        "dataset_id": experiment["dataset_id"],
        "dataset_version_id": experiment["dataset_version_id"],
        "task_runs": len(experiment["task_runs"]),
        "evaluation_runs": len(experiment["evaluation_runs"]),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if passed else 1


def dataset_examples(cases: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {
            "id": str(case["id"]),
            "input": {"message": str(case["input"])},
            "output": {
                "expected_tool": case.get("expected_tool"),
                "expected_arguments": dict(case.get("expected_arguments", {})),
                "exact_input_argument": case.get("exact_input_argument"),
            },
            "metadata": {"case_id": str(case["id"])},
        }
        for case in cases
    ]


def build_task(*, client: LLMClient, model: str, user_id: str):
    def task(input: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
        response = client.complete(
            LLMRequest(
                operation="eval.mcp_intent_selection",
                model=model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT.format(user_id=user_id)},
                    {"role": "user", "content": str(input["message"])},
                ],
                temperature=0,
                tools=function_tools(),
                tool_choice="auto",
                metadata={
                    "case_id": str(metadata["case_id"]),
                    "selection_only": True,
                },
            )
        )
        return {"tool_calls": response.tool_calls}

    return task


def build_contract_evaluator(*, user_id: str):
    def intent_contract(
        input: dict[str, Any],
        output: dict[str, Any],
        expected: dict[str, Any],
        metadata: dict[str, Any],
    ) -> dict[str, Any]:
        case = {
            "id": str(metadata["case_id"]),
            "input": str(input["message"]),
            **expected,
        }
        result = score_case(case, list(output.get("tool_calls", [])), user_id=user_id)
        return {
            "score": 1 if result["passed"] else 0,
            "label": "passed" if result["passed"] else "failed",
            "explanation": "; ".join(result["reasons"]) or "contract matched",
            "metadata": {"case_id": result["id"]},
        }

    return intent_contract


def evaluation_passed(evaluation_run: dict[str, Any]) -> bool:
    if evaluation_run.get("error"):
        return False
    result = evaluation_run.get("result")
    if isinstance(result, list):
        return bool(result) and all(item.get("score") == 1 for item in result)
    return isinstance(result, dict) and result.get("score") == 1


if __name__ == "__main__":
    raise SystemExit(main())
