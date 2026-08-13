"""Tests for the tokenizer."""

from __future__ import annotations

import pytest

from calculator.errors import TokenizeError
from calculator.tokenizer import Tokenizer
from calculator.tokens import TokenType


def types(source: str) -> list[TokenType]:
    return [t.type for t in Tokenizer(source).tokenize()]


def test_operators_and_parens():
    assert types("+ - ( )") == [
        TokenType.PLUS,
        TokenType.MINUS,
        TokenType.LPAREN,
        TokenType.RPAREN,
        TokenType.EOF,
    ]


def test_whitespace_is_ignored():
    assert types("  1   +2 ") == [
        TokenType.NUMBER,
        TokenType.PLUS,
        TokenType.NUMBER,
        TokenType.EOF,
    ]


def test_integer_value():
    (token, _eof) = Tokenizer("42").tokenize()
    assert token.type is TokenType.NUMBER
    assert token.value == 42
    assert isinstance(token.value, int)


def test_decimal_value():
    (token, _eof) = Tokenizer("3.14").tokenize()
    assert token.value == pytest.approx(3.14)
    assert isinstance(token.value, float)


def test_positions_are_tracked():
    tokens = Tokenizer("1 + 20").tokenize()
    assert [t.position for t in tokens] == [0, 2, 4, 6]


def test_unknown_character_raises():
    with pytest.raises(TokenizeError):
        Tokenizer("1 * 2").tokenize()


def test_double_dot_number_raises():
    with pytest.raises(TokenizeError):
        Tokenizer("1.2.3").tokenize()


def test_lone_dot_raises():
    with pytest.raises(TokenizeError):
        Tokenizer(".").tokenize()


def test_empty_source_yields_only_eof():
    assert types("") == [TokenType.EOF]
