"""Token definitions shared by the tokenizer and the parser."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto


class TokenType(Enum):
    """The kinds of token this calculator understands."""

    NUMBER = auto()
    PLUS = auto()
    MINUS = auto()
    LPAREN = auto()
    RPAREN = auto()
    EOF = auto()


@dataclass(frozen=True)
class Token:
    """A single lexical unit produced by the tokenizer.

    ``value`` holds the numeric value for ``NUMBER`` tokens and is ``None``
    otherwise. ``position`` is the 0-based index of the token in the source
    string, used to build helpful error messages.
    """

    type: TokenType
    position: int
    value: float | int | None = None

    def __str__(self) -> str:  # pragma: no cover - cosmetic only
        if self.type is TokenType.NUMBER:
            return f"NUMBER({self.value})"
        return self.type.name
