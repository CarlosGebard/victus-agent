from __future__ import annotations

import argparse
import asyncio
import json
import os
import subprocess
import sys

ALEMBIC_CONFIG = "ops/db/alembic.ini"


def main() -> int:
    parser = argparse.ArgumentParser(description="Victus development CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    test_parser = subparsers.add_parser("test", help="Run the pytest suite.")
    test_parser.add_argument("pytest_args", nargs="*", help="Additional pytest arguments.")

    subparsers.add_parser("compile", help="Compile src and tests.")
    subparsers.add_parser("check", help="Run tests and compile checks.")
    graph_dev_parser = subparsers.add_parser("graph-dev", help="Start LangGraph dev server.")
    graph_dev_parser.add_argument(
        "langgraph_args",
        nargs=argparse.REMAINDER,
        help="Additional langgraph dev args.",
    )
    subparsers.add_parser("login", help="Authenticate with Victus using browser OAuth PKCE.")
    subparsers.add_parser("logout", help="Remove the local Victus session.")
    subparsers.add_parser("mcp-list-tools", help="List tools exposed by the local Victus MCP server.")
    mcp_call_parser = subparsers.add_parser("mcp-call", help="Call one local Victus MCP tool.")
    mcp_call_parser.add_argument("tool_name")
    mcp_call_parser.add_argument("arguments_json")
    subparsers.add_parser("tools-list", help="List tools from the Victus catalog.")
    inspect_parser = subparsers.add_parser("tool-inspect", help="Inspect one tool contract.")
    inspect_parser.add_argument("tool_name")
    run_parser = subparsers.add_parser("tool-run", help="Run one tool through the shared runtime.")
    run_parser.add_argument("tool_name")
    run_parser.add_argument("arguments_json")
    subparsers.add_parser("db-upgrade", help="Run Alembic migrations to head.")
    subparsers.add_parser("db-current", help="Show current Alembic revision.")
    subparsers.add_parser(
        "langgraph-storage-setup",
        help="Create or upgrade LangGraph checkpoint and Store tables.",
    )
    subparsers.add_parser("smoke-event-store", help="Append and replay one local test event.")
    subparsers.add_parser("smoke-projections", help="Write and read one local projection row.")
    subparsers.add_parser("smoke-projectors", help="Replay one event into local projections.")
    self_harm_parser = subparsers.add_parser(
        "self-harm-response",
        help="Run SafetyPrecheck and SelfHarmResponse for one English query.",
    )
    self_harm_parser.add_argument("query", help="English user query to evaluate.")
    safety_check_parser = subparsers.add_parser(
        "safety-check",
        help="Classify one prompt with Llama Guard through Hugging Face Router.",
    )
    safety_check_parser.add_argument("query", help="User prompt to evaluate.")
    rebuild_parser = subparsers.add_parser("projections-rebuild", help="Rebuild projections for a user.")
    rebuild_parser.add_argument("user_id")
    intent_eval_parser = subparsers.add_parser(
        "intent-eval",
        help="Evaluate tool selection through LiteLLM without executing tools.",
    )
    intent_eval_parser.add_argument("--cases", default="ops/evals/mcp_intent_cases.json")
    intent_eval_parser.add_argument(
        "--model",
        default=os.getenv("INTENT_EVAL_MODEL", "litellm_proxy/gemini-flash-lite"),
    )
    intent_eval_parser.add_argument("--user-id", default="mcp-smoke-user")
    phoenix_intent_eval_parser = subparsers.add_parser(
        "phoenix-intent-eval",
        help="Run tool-selection cases as a Phoenix experiment.",
    )
    phoenix_intent_eval_parser.add_argument("--cases", default="ops/evals/mcp_intent_cases.json")
    phoenix_intent_eval_parser.add_argument(
        "--model",
        default=os.getenv("INTENT_EVAL_MODEL", "litellm_proxy/gemini-flash-lite"),
    )
    phoenix_intent_eval_parser.add_argument("--user-id", default="mcp-smoke-user")
    phoenix_intent_eval_parser.add_argument("--dataset", default="victus-mcp-intent")
    phoenix_intent_eval_parser.add_argument("--dry-run", type=int, default=0)

    args = parser.parse_args()

    if args.command == "test":
        return _run([sys.executable, "-m", "pytest", *args.pytest_args])
    if args.command == "compile":
        return _run([sys.executable, "-m", "compileall", "src", "tests"])
    if args.command == "check":
        test_code = _run([sys.executable, "-m", "pytest"])
        if test_code != 0:
            return test_code
        return _run([sys.executable, "-m", "compileall", "src", "tests"])
    if args.command == "graph-dev":
        return _run(["langgraph", "dev", "--config", "langgraph.json", *args.langgraph_args])
    if args.command == "login":
        return _login()
    if args.command == "logout":
        return _logout()
    if args.command == "mcp-list-tools":
        return _mcp_list_tools()
    if args.command == "mcp-call":
        return _mcp_call(args.tool_name, args.arguments_json)
    if args.command == "tools-list":
        return _tools_list()
    if args.command == "tool-inspect":
        return _tool_inspect(args.tool_name)
    if args.command == "tool-run":
        return _mcp_call(args.tool_name, args.arguments_json)
    if args.command == "db-upgrade":
        from victus_platform.database.setup import schema_setup_lock, upgrade_database_schema

        with schema_setup_lock() as url:
            upgrade_database_schema(url)
        return 0
    if args.command == "db-current":
        return _run([sys.executable, "-m", "alembic", "-c", ALEMBIC_CONFIG, "current"])
    if args.command == "langgraph-storage-setup":
        return _langgraph_storage_setup()
    if args.command == "smoke-event-store":
        return _smoke_event_store()
    if args.command == "smoke-projections":
        return _smoke_projections()
    if args.command == "smoke-projectors":
        return _smoke_projectors()
    if args.command == "self-harm-response":
        return _self_harm_response(args.query)
    if args.command == "safety-check":
        return _safety_check(args.query)
    if args.command == "projections-rebuild":
        return _projections_rebuild(args.user_id)
    if args.command == "intent-eval":
        from ops.scripts.mcp_intent_eval import main as intent_eval_main

        return intent_eval_main(
            [
                "--cases",
                args.cases,
                "--model",
                args.model,
                "--user-id",
                args.user_id,
            ]
        )
    if args.command == "phoenix-intent-eval":
        from ops.scripts.phoenix_intent_eval import main as phoenix_intent_eval_main

        return phoenix_intent_eval_main(
            [
                "--cases",
                args.cases,
                "--model",
                args.model,
                "--user-id",
                args.user_id,
                "--dataset",
                args.dataset,
                "--dry-run",
                str(args.dry_run),
            ]
        )

    parser.error(f"unknown command: {args.command}")
    return 2


def _run(command: list[str]) -> int:
    return subprocess.run(command, check=False).returncode


def _login() -> int:
    from adapters.cli.auth import LoginError, run_browser_login

    try:
        result = run_browser_login()
    except LoginError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(f"Victus session saved at {result.session_path}")
    return 0


def _logout() -> int:
    from victus_platform.identity.local_session import delete_local_session

    removed = delete_local_session()
    print("Victus session removed." if removed else "No local Victus session found.")
    return 0


def _mcp_list_tools() -> int:
    return _tools_list()


def _tools_list() -> int:
    from adapters.cli.commands import list_tool_data
    from adapters.cli.rendering import render_json

    render_json(list_tool_data())
    return 0


def _tool_inspect(tool_name: str) -> int:
    from adapters.cli.commands import inspect_tool
    from adapters.cli.rendering import render_json

    render_json(inspect_tool(tool_name))
    return 0


def _mcp_call(tool_name: str, arguments_json: str) -> int:
    from adapters.cli.commands import invoke_tool
    from adapters.cli.rendering import render_json

    try:
        arguments = json.loads(arguments_json)
    except json.JSONDecodeError as exc:
        print(f"invalid arguments JSON: {exc}", file=sys.stderr)
        return 2
    if not isinstance(arguments, dict):
        print("arguments JSON must be an object", file=sys.stderr)
        return 2

    result = asyncio.run(invoke_tool(tool_name, arguments))
    render_json(result)
    return 0


def _smoke_event_store() -> int:
    from datetime import UTC, datetime
    from uuid import uuid4

    from victus_platform.database.engine import build_engine
    from domain.events.envelope import EventActor, UserEventEnvelope
    from domain.events.nutrition import MealLoggedPayload
    from victus_platform.repositories.events import PostgresEventStore

    now = datetime.now(UTC).isoformat()
    user_id = "local-smoke-user"
    idempotency_key = f"smoke:{uuid4()}"
    event = UserEventEnvelope(
        event_id=str(uuid4()),
        event_seq=0,
        user_id=user_id,
        event_type="meal.logged",
        aggregate_type="meal",
        aggregate_id=str(uuid4()),
        occurred_at=now,
        recorded_at=now,
        source="test",
        actor=EventActor(actor_type="tool", actor_id="smoke-event-store"),
        idempotency_key=idempotency_key,
        payload=MealLoggedPayload(
            meal_id=str(uuid4()),
            meal_type="snack",
            consumed_at=now,
            source="manual",
            items=[],
        ),
    )

    engine = build_engine()
    with engine.begin() as connection:
        store = PostgresEventStore(connection)
        appended = store.append(event)
        repeated = store.append(event)
        events = store.list_for_user(user_id, after_seq=0, limit=5)

    if appended.event_id != repeated.event_id:
        print("idempotency check failed", file=sys.stderr)
        return 1
    if not events:
        print("event replay check failed", file=sys.stderr)
        return 1

    print(f"event_store_ok event_seq={appended.event_seq} event_id={appended.event_id}")
    return 0


def _langgraph_storage_setup() -> int:
    from adapters.langgraph.runtime.persistence import setup_postgres_graph_storage
    from victus_platform.database.engine import database_url

    asyncio.run(setup_postgres_graph_storage(database_url()))
    print("langgraph_storage_ok")
    return 0


def _self_harm_response(query: str) -> int:
    import json

    from adapters.langgraph.capabilities.self_harm_response import self_harm_response

    state = {
        "request": {
            "original_text": query,
            "working_text": query,
        }
    }
    state["safety"] = _self_harm_safety_state(query)
    state = self_harm_response()(state)
    print(
        json.dumps(
            {
                "safety": state.get("safety", {}),
                "response": state.get("response", {}),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _self_harm_safety_state(query: str) -> dict[str, object]:
    try:
        from safety.engine.safety_precheck import SafetyPrecheck
        from safety.engine.schemas import SafetyPrecheckInput
    except ModuleNotFoundError:
        text = query.lower()
        is_self_harm = any(term in text for term in ["kill myself", "hurt myself", "suicide"])
        return {
            "status": "blocked" if is_self_harm else "ok",
            "reasons": ["local_self_harm_keyword"] if is_self_harm else [],
            "decision": "route_to_safety_triage" if is_self_harm else "allow",
            "severity": "high" if is_self_harm else "none",
            "categories": ["self_harm"] if is_self_harm else ["none"],
        }

    result = SafetyPrecheck().check(
        SafetyPrecheckInput(
            original_text=query,
            working_text=query,
        )
    )
    return {
        "status": "ok" if result.decision == "allow" else "blocked",
        "reasons": result.reasons,
        "decision": result.decision,
        "severity": result.severity,
        "categories": result.categories,
    }


def _safety_check(query: str) -> int:
    import json

    from adapters.langgraph.runtime.context import _safety_from_llama_guard
    from victus_platform.config.runtime import load_runtime_config
    from victus_platform.llm.hugging_face_endpoint import (
        HuggingFaceRouterClient,
        hugging_face_router_base_url_from_env,
        hugging_face_token_from_env,
    )

    config = load_runtime_config()
    try:
        response = HuggingFaceRouterClient(
            base_url=hugging_face_router_base_url_from_env(),
            token=hugging_face_token_from_env(),
        ).complete_guard(model=config.safety.model, user_text=query)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    safety = _safety_from_llama_guard(response.text)
    print(
        json.dumps(
            {
                "model": config.safety.model,
                "source": "hugging_face_router",
                "input": query,
                "raw_response": response.text,
                "safety": safety,
                "raw": response.raw,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


def _smoke_projections() -> int:
    from datetime import UTC, datetime

    from victus_platform.database.engine import build_engine
    from domain.projections.models import UserProfileProjection
    from victus_platform.repositories.projections import ProjectionRepository

    now = datetime.now(UTC).isoformat()
    user_id = "local-smoke-user"
    projection = UserProfileProjection(user_id=user_id, last_event_seq=0, updated_at=now)

    engine = build_engine()
    with engine.begin() as connection:
        repository = ProjectionRepository(connection)
        repository.save_user_profile(projection)
        repository.save_offset("smoke.user_profile", 0)
        loaded = repository.get_user_profile(user_id)
        offset = repository.get_offset("smoke.user_profile")

    if loaded is None:
        print("projection read check failed", file=sys.stderr)
        return 1

    print(f"projections_ok user_id={loaded.user_id} offset={offset}")
    return 0


def _smoke_projectors() -> int:
    from datetime import UTC, datetime
    from uuid import uuid4

    from victus_platform.database.engine import build_engine
    from domain.events.envelope import EventActor, UserEventEnvelope
    from domain.events.nutrition import MealLoggedPayload
    from victus_platform.repositories.events import PostgresEventStore
    from victus_platform.repositories.projections import ProjectionRepository
    from victus_platform.repositories.rebuild import rebuild_nutrition_status

    now = datetime.now(UTC).isoformat()
    user_id = "local-smoke-user"
    meal_id = str(uuid4())
    event = UserEventEnvelope(
        event_id=str(uuid4()),
        event_seq=0,
        user_id=user_id,
        event_type="meal.logged",
        aggregate_type="meal",
        aggregate_id=meal_id,
        occurred_at=now,
        recorded_at=now,
        source="test",
        actor=EventActor(actor_type="tool", actor_id="smoke-projectors"),
        idempotency_key=f"projector-smoke:{meal_id}",
        payload=MealLoggedPayload(
            meal_id=meal_id,
            meal_type="snack",
            consumed_at=now,
            source="manual",
            items=[],
        ),
    )

    engine = build_engine()
    with engine.begin() as connection:
        event_store = PostgresEventStore(connection)
        projections = ProjectionRepository(connection)
        appended = event_store.append(event)
        rebuild_nutrition_status(
            user_id=user_id,
            event_store=event_store,
            projections=projections,
        )
        nutrition = projections.get_nutrition_status(user_id)

    if nutrition is None or not any(meal.meal_id == meal_id for meal in nutrition.recent_meals):
        print("projector replay check failed", file=sys.stderr)
        return 1

    print(f"projectors_ok event_seq={appended.event_seq} meal_id={meal_id}")
    return 0


def _projections_rebuild(user_id: str) -> int:
    from victus_platform.database.engine import build_engine
    from victus_platform.repositories.events import PostgresEventStore
    from victus_platform.repositories.projections import ProjectionRepository
    from victus_platform.repositories.rebuild import rebuild_all_for_user

    engine = build_engine()
    with engine.begin() as connection:
        result = rebuild_all_for_user(
            user_id=user_id,
            event_store=PostgresEventStore(connection),
            projections=ProjectionRepository(connection),
        )

    rendered = " ".join(f"{name}={seq}" for name, seq in sorted(result.items()))
    print(f"projections_rebuild_ok user_id={user_id} {rendered}")
    return 0
