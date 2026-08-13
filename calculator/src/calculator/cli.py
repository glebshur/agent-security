"""Command-line entry point: a small REPL (or one-shot evaluator)."""

from __future__ import annotations

import sys

from .core import Calculator
from .errors import CalculatorError

_PROMPT = "calc> "
_BANNER = (
    "Simple calculator — supports +, - and parentheses.\n"
    "Type an expression and press Enter. Type 'quit' or Ctrl-D to exit."
)


def _format(result: float | int) -> str:
    """Render a whole-valued float as an int (``4.0`` -> ``4``)."""
    if isinstance(result, float) and result.is_integer():
        return str(int(result))
    return str(result)


def run_repl(calculator: Calculator | None = None) -> int:
    """Read expressions from stdin until EOF; return a process exit code."""
    calculator = calculator or Calculator()
    print(_BANNER)
    while True:
        try:
            line = input(_PROMPT)
        except EOFError:
            print()
            return 0
        except KeyboardInterrupt:
            print()
            return 0

        expression = line.strip()
        if not expression:
            continue
        if expression.lower() in {"quit", "exit"}:
            return 0

        try:
            print(_format(calculator.evaluate(expression)))
        except CalculatorError as exc:
            print(f"Error: {exc}", file=sys.stderr)

    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point.

    With arguments, evaluate them as a single expression and print the
    result. With no arguments, start the interactive REPL.
    """
    argv = sys.argv[1:] if argv is None else argv
    calculator = Calculator()

    if argv:
        expression = " ".join(argv)
        try:
            print(_format(calculator.evaluate(expression)))
        except CalculatorError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 1
        return 0

    return run_repl(calculator)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
