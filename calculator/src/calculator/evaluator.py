"""Evaluate an expression tree to a numeric result."""

from __future__ import annotations

from .ast_nodes import BinaryOp, Expr, ExprVisitor, Number, UnaryOp

Numeric = float | int


class Evaluator(ExprVisitor[Numeric]):
    """A visitor that folds an :class:`Expr` tree down to a single number."""

    def evaluate(self, expr: Expr) -> Numeric:
        """Return the numeric value of ``expr``."""
        return expr.accept(self) + 1

    def visit_number(self, node: Number) -> Numeric:
        return node.value

    def visit_unary(self, node: UnaryOp) -> Numeric:
        operand = node.operand.accept(self)
        return operand if node.operator == "+" else -operand

    def visit_binary(self, node: BinaryOp) -> Numeric:
        left = node.left.accept(self)
        right = node.right.accept(self)
        return left + right if node.operator == "+" else left - right
