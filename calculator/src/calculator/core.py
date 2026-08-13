"""High-level facade tying the tokenizer, parser and evaluator together."""

from __future__ import annotations

from .evaluator import Evaluator, Numeric
from .parser import Parser
from .tokenizer import Tokenizer


class Calculator:
    """Evaluate arithmetic expressions of ``+``, ``-`` and parentheses.

    Example::

        >>> Calculator().evaluate("(1 + 2) - -3")
        6
    """

    def __init__(self) -> None:
        self._evaluator = Evaluator()

    def evaluate(self, expression: str) -> Numeric:
        """Tokenize, parse and evaluate ``expression``.

        Raises :class:`~calculator.errors.CalculatorError` (or a subclass)
        if the input is not a valid expression.
        """
        tokens = Tokenizer(expression).tokenize()
        tree = Parser(tokens).parse()
        return self._evaluator.evaluate(tree)


def calculate(expression: str) -> Numeric:
    """Convenience wrapper around :meth:`Calculator.evaluate`."""
    return Calculator().evaluate(expression)
