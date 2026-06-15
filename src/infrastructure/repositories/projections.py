from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import Connection, select
from sqlalchemy.dialects.postgresql import insert

from infrastructure.db.schema import (
    constraint_projection,
    nutrition_status_projection,
    planning_history_projection,
    projector_offsets,
    user_profile_projection,
)
from domain.projections.models import (
    ConstraintProjection,
    NutritionStatusProjection,
    PlanningHistoryProjection,
    UserProfileProjection,
)


class ProjectionRepository:
    def __init__(self, connection: Connection) -> None:
        self.connection = connection

    def get_user_profile(self, user_id: str) -> UserProfileProjection | None:
        row = self.connection.execute(
            select(user_profile_projection).where(user_profile_projection.c.user_id == user_id)
        ).mappings().first()
        return _profile_from_row(dict(row)) if row else None

    def save_user_profile(self, projection: UserProfileProjection) -> None:
        values = {
            "user_id": projection.user_id,
            "profile": projection.profile.model_dump(exclude_none=True),
            "restrictions": [item.model_dump(exclude_none=True) for item in projection.restrictions],
            "preferences": [item.model_dump(exclude_none=True) for item in projection.preferences],
            "active_goal_id": projection.active_goal_id,
            "last_event_seq": projection.last_event_seq,
            "updated_at": _from_iso(projection.updated_at),
        }
        statement = insert(user_profile_projection).values(**values)
        self.connection.execute(
            statement.on_conflict_do_update(
                index_elements=[user_profile_projection.c.user_id],
                set_=values,
            )
        )

    def get_nutrition_status(self, user_id: str) -> NutritionStatusProjection | None:
        row = self.connection.execute(
            select(nutrition_status_projection).where(
                nutrition_status_projection.c.user_id == user_id
            )
        ).mappings().first()
        return _nutrition_from_row(dict(row)) if row else None

    def save_nutrition_status(self, projection: NutritionStatusProjection) -> None:
        values = {
            "user_id": projection.user_id,
            "recent_meals": [item.model_dump(exclude_none=True) for item in projection.recent_meals],
            "biometrics": projection.biometrics.model_dump(exclude_none=True),
            "symptoms": [item.model_dump(exclude_none=True) for item in projection.symptoms],
            "computed_metrics": projection.computed_metrics.model_dump(exclude_none=True),
            "last_event_seq": projection.last_event_seq,
            "updated_at": _from_iso(projection.updated_at),
        }
        statement = insert(nutrition_status_projection).values(**values)
        self.connection.execute(
            statement.on_conflict_do_update(
                index_elements=[nutrition_status_projection.c.user_id],
                set_=values,
            )
        )

    def get_constraint(self, user_id: str) -> ConstraintProjection | None:
        row = self.connection.execute(
            select(constraint_projection).where(constraint_projection.c.user_id == user_id)
        ).mappings().first()
        return _constraint_from_row(dict(row)) if row else None

    def save_constraint(self, projection: ConstraintProjection) -> None:
        values = {
            "user_id": projection.user_id,
            "hard_constraints": [
                item.model_dump(exclude_none=True) for item in projection.hard_constraints
            ],
            "soft_constraints": [
                item.model_dump(exclude_none=True) for item in projection.soft_constraints
            ],
            "safety_flags": [item.model_dump(exclude_none=True) for item in projection.safety_flags],
            "derived_from_event_seq": projection.derived_from_event_seq,
            "updated_at": _from_iso(projection.updated_at),
        }
        statement = insert(constraint_projection).values(**values)
        self.connection.execute(
            statement.on_conflict_do_update(
                index_elements=[constraint_projection.c.user_id],
                set_=values,
            )
        )

    def get_planning_history(self, user_id: str) -> PlanningHistoryProjection | None:
        row = self.connection.execute(
            select(planning_history_projection).where(
                planning_history_projection.c.user_id == user_id
            )
        ).mappings().first()
        return _planning_from_row(dict(row)) if row else None

    def save_planning_history(self, projection: PlanningHistoryProjection) -> None:
        values = {
            "user_id": projection.user_id,
            "active_session_id": projection.active_session_id,
            "active_plan_artifact_id": projection.active_plan_artifact_id,
            "active_goal_id": projection.active_goal_id,
            "revision_summary": [
                item.model_dump(exclude_none=True) for item in projection.revision_summary
            ],
            "feedback_summary": [
                item.model_dump(exclude_none=True) for item in projection.feedback_summary
            ],
            "last_event_seq": projection.last_event_seq,
            "updated_at": _from_iso(projection.updated_at),
        }
        statement = insert(planning_history_projection).values(**values)
        self.connection.execute(
            statement.on_conflict_do_update(
                index_elements=[planning_history_projection.c.user_id],
                set_=values,
            )
        )

    def save_offset(self, projector_name: str, last_event_seq: int) -> None:
        values = {"projector_name": projector_name, "last_event_seq": last_event_seq}
        statement = insert(projector_offsets).values(**values)
        self.connection.execute(
            statement.on_conflict_do_update(
                index_elements=[projector_offsets.c.projector_name],
                set_={"last_event_seq": last_event_seq, "updated_at": datetime.now(UTC)},
            )
        )

    def get_offset(self, projector_name: str) -> int:
        row = self.connection.execute(
            select(projector_offsets.c.last_event_seq).where(
                projector_offsets.c.projector_name == projector_name
            )
        ).first()
        return int(row[0]) if row else 0


def empty_projection_rows(user_id: str, updated_at: str) -> dict[str, Any]:
    return {
        "user_profile": UserProfileProjection(user_id=user_id, last_event_seq=0, updated_at=updated_at),
        "constraint": ConstraintProjection(
            user_id=user_id,
            derived_from_event_seq=0,
            updated_at=updated_at,
        ),
        "nutrition_status": NutritionStatusProjection(
            user_id=user_id,
            last_event_seq=0,
            updated_at=updated_at,
        ),
        "planning_history": PlanningHistoryProjection(
            user_id=user_id,
            last_event_seq=0,
            updated_at=updated_at,
        ),
    }


def _profile_from_row(row: dict[str, Any]) -> UserProfileProjection:
    return UserProfileProjection(
        user_id=row["user_id"],
        profile=row["profile"],
        restrictions=row["restrictions"],
        preferences=row["preferences"],
        active_goal_id=row["active_goal_id"],
        last_event_seq=row["last_event_seq"],
        updated_at=_to_iso(row["updated_at"]),
    )


def _nutrition_from_row(row: dict[str, Any]) -> NutritionStatusProjection:
    return NutritionStatusProjection(
        user_id=row["user_id"],
        recent_meals=row["recent_meals"],
        biometrics=row["biometrics"],
        symptoms=row["symptoms"],
        computed_metrics=row["computed_metrics"],
        last_event_seq=row["last_event_seq"],
        updated_at=_to_iso(row["updated_at"]),
    )


def _constraint_from_row(row: dict[str, Any]) -> ConstraintProjection:
    return ConstraintProjection(
        user_id=row["user_id"],
        hard_constraints=row["hard_constraints"],
        soft_constraints=row["soft_constraints"],
        safety_flags=row["safety_flags"],
        derived_from_event_seq=row["derived_from_event_seq"],
        updated_at=_to_iso(row["updated_at"]),
    )


def _planning_from_row(row: dict[str, Any]) -> PlanningHistoryProjection:
    return PlanningHistoryProjection(
        user_id=row["user_id"],
        active_session_id=row["active_session_id"],
        active_plan_artifact_id=row["active_plan_artifact_id"],
        active_goal_id=row["active_goal_id"],
        revision_summary=row["revision_summary"],
        feedback_summary=row["feedback_summary"],
        last_event_seq=row["last_event_seq"],
        updated_at=_to_iso(row["updated_at"]),
    )


def _to_iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _from_iso(value: str) -> datetime | str:
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
