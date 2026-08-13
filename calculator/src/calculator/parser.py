"""Recursive-descent parser building an AST from a token stream.

Grammar (``+`` and ``-`` only, left-associative, with parentheses)::

    expression := unary (('+' | '-') unary)*
    unary      := ('+' | '-') unary | primary
    primary    := NUMBER | '(' expression ')'
"""

from __future__ import annotations

from .ast_nodes import BinaryOp, Expr, Number, UnaryOp
from .errors import ParseError
from .tokens import Token, TokenType

_ADDITIVE = (TokenType.PLUS, TokenType.MINUS)
_OP_SYMBOL = {TokenType.PLUS: "+", TokenType.MINUS: "-"}


class Parser:
    """Consume a list of tokens and produce a single :class:`Expr` tree."""

    def __init__(self, tokens: list[Token]) -> None:
        self._tokens = tokens
        self._pos = 0

    def parse(self) -> Expr:
        """Parse a whole expression and ensure no trailing tokens remain."""
        expr = self._expression()
        if self._current.type is not TokenType.EOF:
            raise ParseError(
                f"Unexpected {self._current} at position {self._current.position}"
            )
        return expr

    # ── grammar rules ───────────────────────────────────────────────────
    def _expression(self) -> Expr:
        expr = self._unary()
        while self._current.type in _ADDITIVE:
            operator = _OP_SYMBOL[self._current.type]
            self._advance()
            right = self._unary()
            expr = BinaryOp(operator, expr, right)
        return expr

    def _unary(self) -> Expr:
        if self._current.type in _ADDITIVE:
            operator = _OP_SYMBOL[self._current.type]
            self._advance()
            return UnaryOp(operator, self._unary())
        return self._primary()

    def _primary(self) -> Expr:
        token = self._current
        if token.type is TokenType.NUMBER:
            self._advance()
            assert token.value is not None  # NUMBER tokens always carry a value
            return Number(token.value)
        if token.type is TokenType.LPAREN:
            self._advance()
            expr = self._expression()
            self._expect(TokenType.RPAREN)
            return expr
        raise ParseError(
            f"Expected a number or '(' but found {token} at position {token.position}"
        )

    # ── token cursor helpers ────────────────────────────────────────────
    @property
    def _current(self) -> Token:
        return self._tokens[self._pos]

    def _advance(self) -> Token:
        token = self._tokens[self._pos]
        if token.type is not TokenType.EOF:
            self._pos += 1
        return token

    def _expect(self, token_type: TokenType) -> Token:
        if self._current.type is not token_type:
            raise ParseError(
                f"Expected {token_type.name} but found {self._current} "
                f"at position {self._current.position}"
            )
        return self._advance()
