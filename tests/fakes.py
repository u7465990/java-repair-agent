"""Shared deterministic doubles for tests."""

from __future__ import annotations

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from pydantic import PrivateAttr

from java_agent.sandbox.base import ExecResult


class ScriptedChatModel(BaseChatModel):
    """Returns a fixed sequence of AI messages, ignoring the prompt."""

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
    def __init__(self, output: str = "1\tclass X {}", exit_code: int = 0) -> None:
        self.calls: list[list[str]] = []
        self.output = output
        self.exit_code = exit_code

    def exec(self, args, cwd=None, timeout=600) -> ExecResult:
        self.calls.append(list(args))
        return ExecResult(self.exit_code, self.output, "")

    def close(self) -> None:
        return None
