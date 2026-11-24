"""A small ReAct loop built on LangGraph."""

from __future__ import annotations

from typing import Annotated, TypedDict

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AnyMessage, SystemMessage, ToolMessage
from langchain_core.tools import BaseTool
from langgraph.graph import END, START, StateGraph
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    steps: int


def _compact(messages: list[AnyMessage], keep: int) -> list[AnyMessage]:
    """Keep a recent tail, never starting with an orphaned tool result."""
    if keep <= 0 or len(messages) <= keep:
        return messages
    tail = list(messages[-keep:])
    while tail and isinstance(tail[0], ToolMessage):
        tail.pop(0)
    return tail


def build_react_agent(
    model: BaseChatModel,
    tools: list[BaseTool],
    system_prompt: str,
    max_steps: int = 40,
    keep_messages: int = 12,
):
    """Compile a tool-calling loop that stops on finish, plain text or budget."""
    bound = model.bind_tools(tools)
    tool_node = ToolNode(tools)

    def call_model(state: AgentState) -> dict:
        history = _compact(state["messages"], keep_messages)
        messages = [SystemMessage(content=system_prompt), *history]
        response = bound.invoke(messages)
        return {"messages": [response], "steps": state.get("steps", 0) + 1}

    def after_agent(state: AgentState) -> str:
        last = state["messages"][-1]
        calls = getattr(last, "tool_calls", None) or []
        if not calls:
            return "end"
        if any(call.get("name") == "finish" for call in calls):
            return "end"
        if state.get("steps", 0) >= max_steps:
            return "end"
        return "tools"

    graph = StateGraph(AgentState)
    graph.add_node("agent", call_model)
    graph.add_node("tools", tool_node)
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", after_agent, {"tools": "tools", "end": END})
    graph.add_edge("tools", "agent")
    return graph.compile()
