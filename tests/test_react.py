from fakes import FakeSandbox, ScriptedChatModel
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from java_agent.agent.react import _compact, build_react_agent
from java_agent.tools import ToolContext, build_tools


def _call(name: str, args: dict, call_id: str) -> AIMessage:
    return AIMessage(
        content="",
        tool_calls=[{"name": name, "args": args, "id": call_id, "type": "tool_call"}],
    )


def test_agent_calls_tool_then_finishes() -> None:
    sandbox = FakeSandbox()
    tools = build_tools(ToolContext(sandbox, "/workspace/repo"))
    model = ScriptedChatModel(
        responses=[
            _call("read_file", {"path": "src/X.java"}, "c1"),
            _call("finish", {"summary": "done"}, "c2"),
        ]
    )
    agent = build_react_agent(model, tools, "system prompt", max_steps=5)
    state = agent.invoke({"messages": [HumanMessage(content="fix it")]})

    assert state["steps"] == 2
    assert any(isinstance(message, ToolMessage) for message in state["messages"])
    assert sandbox.calls


def test_compact_never_starts_with_orphaned_tool_result() -> None:
    messages = [
        HumanMessage(content="start"),
        AIMessage(
            content="",
            tool_calls=[{"name": "read_file", "args": {"path": "x"}, "id": "c1", "type": "tool_call"}],
        ),
        ToolMessage(content="file", tool_call_id="c1"),
        HumanMessage(content="next"),
    ]
    compacted = _compact(messages, 2)
    assert len(compacted) == 1
    assert isinstance(compacted[0], HumanMessage)


def test_agent_stops_at_step_budget() -> None:
    sandbox = FakeSandbox()
    tools = build_tools(ToolContext(sandbox, "/workspace/repo"))
    model = ScriptedChatModel(responses=[_call("read_file", {"path": "src/X.java"}, "c1")])
    agent = build_react_agent(model, tools, "system prompt", max_steps=2)
    state = agent.invoke({"messages": [HumanMessage(content="loop")]})

    assert state["steps"] == 2
