from application.ports.llm import LLMRequest, LLMResponse


def test_llm_request_keeps_operation_model_messages_and_metadata() -> None:
    request = LLMRequest(
        operation="test.operation",
        model="litellm_proxy/test",
        messages=[{"role": "user", "content": "hello"}],
        metadata={"entity_id": "entity-1"},
    )

    assert request.operation == "test.operation"
    assert request.model == "litellm_proxy/test"
    assert request.messages[0]["content"] == "hello"
    assert request.metadata == {"entity_id": "entity-1"}


def test_llm_response_separates_text_raw_and_usage() -> None:
    response = LLMResponse(text="ok", raw={"id": "completion-1"}, usage={"total_tokens": 3})

    assert response.text == "ok"
    assert response.raw["id"] == "completion-1"
    assert response.usage["total_tokens"] == 3
