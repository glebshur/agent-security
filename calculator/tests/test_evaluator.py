"""End-to-end tests for evaluating expressions via the Calculator facade."""

from __future__ import annotations

import pytest

from calculator import Calculator, calculate
from calculator.errors import CalculatorError, ParseError, TokenizeError


@pytest.fixture
def calc() -> Calculator:
    return Calculator()


@pytest.mark.parametrize(
    ("expression", "expected"),
    [
        ("1 + 2", 3),
        ("5 - 3", 2),
        ("10 - 3 - 2", 5),          # left-associative
        ("1 + 2 + 3 + 4", 10),
        ("(1 + 2) - (3 - 4)", 4),   # parentheses
        ("((7))", 7),               # nested parentheses
        ("-5", -5),                 # unary minus
        ("2 - -3", 5),              # binary minus then unary minus
        ("-(3 + 4)", -7),           # unary applied to a group
        ("+9", 9),                  # unary plus
        ("  1   +   2  ", 3),       # whitespace
        ("1.5 + 2.5", 4),           # decimals
    ],
)
def test_evaluates_correctly(calc, expression, expected):
    assert calc.evaluate(expression) == expected


def test_calculate_convenience_wrapper():
    assert calculate("(1 + 2) - -3") == 6


def test_unbalanced_parenthesis_raises(calc):
    with pytest.raises(ParseError):
        calc.evaluate("(1 + 2")


def test_unknown_operator_raises_tokenize_error(calc):
    with pytest.raises(TokenizeError):
        calc.evaluate("2 * 2")


def test_errors_share_a_common_base(calc):
    # A caller can catch every failure mode with the one base class.
    with pytest.raises(CalculatorError):
        calc.evaluate("1 +")
