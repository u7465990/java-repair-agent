"""Token usage accounting."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Usage:
    """Aggregated token usage for a repair run."""

    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens

    def add(self, other: Usage) -> None:
        self.calls += other.calls
        self.input_tokens += other.input_tokens
        self.output_tokens += other.output_tokens

    def cost_usd(self, price_in_per_million: float, price_out_per_million: float) -> float:
        return (
            self.input_tokens / 1_000_000 * price_in_per_million
            + self.output_tokens / 1_000_000 * price_out_per_million
        )


def usage_from_messages(messages: list) -> Usage:
    """Sum usage_metadata reported by the chat model on assistant messages."""
    total = Usage()
    for message in messages:
        metadata = getattr(message, "usage_metadata", None)
        if not metadata:
            continue
        total.calls += 1
        total.input_tokens += int(metadata.get("input_tokens", 0))
        total.output_tokens += int(metadata.get("output_tokens", 0))
    return total
