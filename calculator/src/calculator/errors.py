"""Exception hierarchy for the calculator.

All errors raised while turning a string into a result derive from
:class:`CalculatorError`, so a caller can catch that single base class.
"""

from __future__ import annotations


class CalculatorError(Exception):
    """Base class for every error the calculator raises."""


class TokenizeError(CalculatorError):
    """The input contains a character the tokenizer does not understand."""


class ParseError(CalculatorError):
    """The tokens do not form a valid expression."""
