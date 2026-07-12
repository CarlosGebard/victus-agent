from application.tools import execute_tool, list_tools


def test_tool_registry_exposes_current_tools() -> None:
    assert [tool.name for tool in list_tools(visible_only=True)] == [
        "event_capture",
        "profile_update",
    ]


def test_event_capture_tool_returns_tool_result() -> None:
    result = execute_tool(
        "event_capture",
        {"user_id": "user-1", "normalized_text": "hoy comi arroz con pollo"},
    )

    assert result.status == "success"
    assert result.data["capture_action"] == "log_meal"
    assert result.meta.handler_version == "event_capture.v1"


def test_profile_update_tool_returns_tool_result() -> None:
    result = execute_tool(
        "profile_update",
        {"user_id": "user-1", "normalized_text": "soy intolerante a la lactosa"},
    )

    assert result.status == "success"
    assert result.data["profile_action"] == "add_restriction"
    assert result.meta.handler_version == "profile_update.v1"
