from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import PrivateAttr

from java_agent.agent.react import build_react_agent
from java_agent.sandbox.base import ExecResult
from java_agent.tools import ToolContext, build_tools


class ScriptedChatModel(BaseChatModel):
    responses: list[AIMessage]
    _index: int = PrivateAttr(default=0)

    def _generate(self, messages: list[BaseMessage], stop=None, run_manager=None, **kwargs):
        index = min(self._index, len(self.responses) - 1)
        self._index += 1
        return ChatResult(generations=[ChatGeneration(message=self.responses[index])])

    @property
    def _llm_type(self) -> str:
        return "scripted"

    def bind_tools(self, tools, **kwargs):
        return self


class FakeSandbox:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def exec(self, args, cwd=None, timeout=600) -> ExecResult:
        self.calls.append(list(args))
        return ExecResult(0, "1\tclass X {}", "")

    def close(self) -> None:
        return None


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


def test_agent_stops_at_step_budget() -> None:
    sandbox = FakeSandbox()
    tools = build_tools(ToolContext(sandbox, "/workspace/repo"))
    model = ScriptedChatModel(responses=[_call("read_file", {"path": "src/X.java"}, "c1")])
    agent = build_react_agent(model, tools, "system prompt", max_steps=2)
    state = agent.invoke({"messages": [HumanMessage(content="loop")]})

    assert state["steps"] == 2
