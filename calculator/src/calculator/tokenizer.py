"""Turn a raw expression string into a list of :class:`Token` objects."""

from __future__ import annotations

from .errors import TokenizeError
from .tokens import Token, TokenType

_SINGLE_CHAR_TOKENS = {
    "+": TokenType.PLUS,
    "-": TokenType.MINUS,
    "(": TokenType.LPAREN,
    ")": TokenType.RPAREN,
}


class Tokenizer:
    """Scan a string left-to-right and emit tokens.

    Numbers may be integers (``42``) or decimals (``3.14``). Whitespace is
    ignored. Any other character raises :class:`TokenizeError`.
    """

    def __init__(self, source: str) -> None:
        self._source = source
        self._pos = 0

    def tokenize(self) -> list[Token]:
        """Return every token in the source, terminated by an ``EOF`` token."""
        tokens: list[Token] = []
        while self._pos < len(self._source):
            char = self._source[self._pos]

            if char.isspace():
                self._pos += 1
                continue

            if char in _SINGLE_CHAR_TOKENS:
                tokens.append(Token(_SINGLE_CHAR_TOKENS[char], self._pos))
                self._pos += 1
                continue

            if char.isdigit() or char == ".":
                tokens.append(self._read_number())
                continue

            raise TokenizeError(
                f"Unexpected character {char!r} at position {self._pos}"
            )

        tokens.append(Token(TokenType.EOF, self._pos))
        return tokens

    def _read_number(self) -> Token:
        start = self._pos
        seen_dot = False
        while self._pos < len(self._source):
            char = self._source[self._pos]
            if char == ".":
                if seen_dot:
                    raise TokenizeError(
                        f"Malformed number: second '.' at position {self._pos}"
                    )
                seen_dot = True
            elif not char.isdigit():
                break
            self._pos += 1

        text = self._source[start : self._pos]
        if text == ".":
            raise TokenizeError(f"Malformed number '.' at position {start}")

        value: float | int = float(text) if seen_dot else int(text)
        return Token(TokenType.NUMBER, start, value)
