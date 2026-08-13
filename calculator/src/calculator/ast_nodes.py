"""Abstract syntax tree nodes and the visitor interface.

The parser builds a tree of :class:`Expr` nodes; an :class:`ExprVisitor`
(such as the evaluator) walks it via the classic *visitor* pattern, so new
operations over the tree can be added without touching the node classes.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

T = TypeVar("T")


class Expr(ABC):
    """Base class for every node in the expression tree."""

    @abstractmethod
    def accept(self, visitor: "ExprVisitor[T]") -> T:
        """Dispatch to the matching ``visit_*`` method on ``visitor``."""


@dataclass(frozen=True)
class Number(Expr):
    """A literal numeric value, e.g. ``42`` or ``3.14``."""

    value: float | int

    def accept(self, visitor: "ExprVisitor[T]") -> T:
        return visitor.visit_number(self)


@dataclass(frozen=True)
class UnaryOp(Expr):
    """A prefix ``+`` or ``-`` applied to a single operand, e.g. ``-x``."""

    operator: str
    operand: Expr

    def accept(self, visitor: "ExprVisitor[T]") -> T:
        return visitor.visit_unary(self)


@dataclass(frozen=True)
class BinaryOp(Expr):
    """A binary ``+`` or ``-`` between two operands, e.g. ``a - b``."""

    operator: str
    left: Expr
    right: Expr

    def accept(self, visitor: "ExprVisitor[T]") -> T:
        return visitor.visit_binary(self)


class ExprVisitor(ABC, Generic[T]):
    """Interface implemented by anything that walks an expression tree."""

    @abstractmethod
    def visit_number(self, node: Number) -> T: ...

    @abstractmethod
    def visit_unary(self, node: UnaryOp) -> T: ...

    @abstractmethod
    def visit_binary(self, node: BinaryOp) -> T: ...
