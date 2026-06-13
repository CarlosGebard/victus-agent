from projections.models import (
    ConstraintProjection,
    NutritionStatusProjection,
    PlanningHistoryProjection,
    UserProfileProjection,
)


def test_projection_defaults_are_empty_collections() -> None:
    profile = UserProfileProjection(user_id="user-1", last_event_seq=0, updated_at="now")
    constraints = ConstraintProjection(user_id="user-1", derived_from_event_seq=0, updated_at="now")
    nutrition = NutritionStatusProjection(user_id="user-1", last_event_seq=0, updated_at="now")
    planning = PlanningHistoryProjection(user_id="user-1", last_event_seq=0, updated_at="now")

    assert profile.restrictions == []
    assert constraints.hard_constraints == []
    assert nutrition.recent_meals == []
    assert planning.revision_summary == []
