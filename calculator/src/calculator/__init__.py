"""A simple OOP calculator supporting ``+``, ``-`` and parentheses.

Public API::

    from calculator import Calculator, calculate

    calculate("(1 + 2) - -3")   # -> 6
"""

from __future__ import annotations

from .cli import main
from .core import Calculator, calculate
from .errors import CalculatorError, ParseError, TokenizeError

__all__ = [
    "Calculator",
    "calculate",
    "main",
    "CalculatorError",
    "ParseError",
    "TokenizeError",
]

__version__ = "0.1.0"
