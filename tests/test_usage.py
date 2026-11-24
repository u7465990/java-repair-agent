from langchain_core.messages import AIMessage

from java_agent.usage import Usage, usage_from_messages


def test_usage_sums_message_metadata() -> None:
    messages = [
        AIMessage(
            content="",
            usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
        ),
        AIMessage(
            content="",
            usage_metadata={"input_tokens": 20, "output_tokens": 7, "total_tokens": 27},
        ),
    ]
    usage = usage_from_messages(messages)
    assert usage.calls == 2
    assert usage.input_tokens == 30
    assert usage.output_tokens == 12
    assert usage.total_tokens == 42


def test_usage_ignores_missing_metadata() -> None:
    assert usage_from_messages([AIMessage(content="hi")]).total_tokens == 0


def test_cost_estimation() -> None:
    usage = Usage(input_tokens=1_000_000, output_tokens=500_000)
    assert usage.cost_usd(1.0, 2.0) == 2.0
