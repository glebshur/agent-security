"""Tests for the recursive-descent parser (structure of the AST)."""

from __future__ import annotations

import pytest

from calculator.ast_nodes import BinaryOp, Number, UnaryOp
from calculator.errors import ParseError
from calculator.parser import Parser
from calculator.tokenizer import Tokenizer


def parse(source: str):
    return Parser(Tokenizer(source).tokenize()).parse()


def test_single_number():
    assert parse("7") == Number(7)


def test_simple_binary():
    assert parse("1 + 2") == BinaryOp("+", Number(1), Number(2))


def test_left_associativity():
    # 10 - 3 - 2 parses as (10 - 3) - 2, not 10 - (3 - 2)
    assert parse("10 - 3 - 2") == BinaryOp(
        "-", BinaryOp("-", Number(10), Number(3)), Number(2)
    )


def test_parentheses_override_grouping():
    assert parse("10 - (3 - 2)") == BinaryOp(
        "-", Number(10), BinaryOp("-", Number(3), Number(2))
    )


def test_unary_minus():
    assert parse("-5") == UnaryOp("-", Number(5))


def test_unary_on_parenthesized_expression():
    assert parse("-(1 + 2)") == UnaryOp("-", BinaryOp("+", Number(1), Number(2)))


@pytest.mark.parametrize("source", ["", "1 +", "+", "(1 + 2", "1 + 2)", "( )", "1 2"])
def test_invalid_expressions_raise(source):
    with pytest.raises(ParseError):
        parse(source)
