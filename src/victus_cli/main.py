from __future__ import annotations

import argparse
import subprocess
import sys


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
    subparsers.add_parser("db-upgrade", help="Run Alembic migrations to head.")
    subparsers.add_parser("db-current", help="Show current Alembic revision.")
    subparsers.add_parser("smoke-event-store", help="Append and replay one local test event.")
    subparsers.add_parser("smoke-projections", help="Write and read one local projection row.")
    subparsers.add_parser("smoke-projectors", help="Replay one event into local projections.")
    rebuild_parser = subparsers.add_parser("projections-rebuild", help="Rebuild projections for a user.")
    rebuild_parser.add_argument("user_id")

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
    if args.command == "db-upgrade":
        return _run([sys.executable, "-m", "alembic", "upgrade", "head"])
    if args.command == "db-current":
        return _run([sys.executable, "-m", "alembic", "current"])
    if args.command == "smoke-event-store":
        return _smoke_event_store()
    if args.command == "smoke-projections":
        return _smoke_projections()
    if args.command == "smoke-projectors":
        return _smoke_projectors()
    if args.command == "projections-rebuild":
        return _projections_rebuild(args.user_id)

    parser.error(f"unknown command: {args.command}")
    return 2


def _run(command: list[str]) -> int:
    return subprocess.run(command, check=False).returncode


def _smoke_event_store() -> int:
    from datetime import UTC, datetime
    from uuid import uuid4

    from infrastructure.db.engine import build_engine
    from domain.events.models import EventActor, MealLoggedPayload, UserEventEnvelope
    from infrastructure.repositories.events import PostgresEventStore

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


def _smoke_projections() -> int:
    from datetime import UTC, datetime

    from infrastructure.db.engine import build_engine
    from domain.projections.models import UserProfileProjection
    from infrastructure.repositories.projections import ProjectionRepository

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

    from infrastructure.db.engine import build_engine
    from domain.events.models import EventActor, MealLoggedPayload, UserEventEnvelope
    from infrastructure.repositories.events import PostgresEventStore
    from infrastructure.repositories.projections import ProjectionRepository
    from application.projections.runner import rebuild_nutrition_status

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
    from infrastructure.db.engine import build_engine
    from infrastructure.repositories.events import PostgresEventStore
    from infrastructure.repositories.projections import ProjectionRepository
    from application.projections.runner import rebuild_all_for_user

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
